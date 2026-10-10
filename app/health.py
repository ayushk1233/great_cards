"""Backend health check: run before launching the UI.

    python -m app.health

Checks config, OpenRouter (auth + model + tool calling) and the MCP server (initialize,
catalog, schema drift vs the recorded discovery catalog, one read-only tool call).
About 1 LLM call and 3 MCP requests. Exit code 0 = healthy.
"""

import asyncio
import json
import sys
import time

from app.config import ROOT, ConfigError, build_limiter, load_settings
from app.mcp.client import McpSession
from app.mcp.tools import ALLOWLIST, build_tool_specs

PROBE_ALIAS = "hdfc-regalia-gold"  # verified working alias (discovery/raw/cards__details_regalia_gold_*)
results: list[tuple[str, str, str]] = []


def report(status: str, name: str, detail: str = "") -> None:
    results.append((status, name, detail))
    print(f"[{status}] {name}{' — ' + detail if detail else ''}")


async def check_mcp(url: str, timeout_s: float, limiter=None) -> list[dict] | None:
    try:
        t0 = time.perf_counter()
        async with McpSession(url, timeout_s, limiter=limiter) as s:
            report("PASS", "mcp initialize", f"{s.server_info} in {round((time.perf_counter() - t0) * 1000)} ms")
            live = await s.list_tools()
            specs = build_tool_specs(live)  # raises if an allowlisted tool vanished
            report("PASS", "mcp catalog", f"{len(live)} tools, all {len(ALLOWLIST)} allowlisted present")
            recorded = json.loads((ROOT / "discovery" / "tools.json").read_text())["tools"]
            if specs == build_tool_specs(recorded):
                report("PASS", "mcp schema drift", "allowlisted schemas identical to discovery/tools.json")
            else:
                report("WARN", "mcp schema drift", "live schemas differ from discovery/tools.json; re-run discovery")
            r = await s.call_tool("get_card_details", {"card_alias": PROBE_ALIAS})
            if r.ok and isinstance(r.data, dict) and r.data.get("name"):
                report("PASS", "mcp tool call", f"get_card_details({PROBE_ALIAS}) -> {r.data['name']} in {r.latency_ms} ms")
            else:
                report("FAIL", "mcp tool call", f"{r.error_kind}: {r.error_msg}")
            return specs
    except Exception as e:
        report("FAIL", "mcp", f"{type(e).__name__}: {e}")
        return None


def check_llm(settings, specs: list[dict] | None) -> None:
    from app.agent.llm import LlmError, OpenRouterLlm

    tools = [t for t in (specs or []) if t["function"]["name"] == "list_cards"] or None
    try:
        t0 = time.perf_counter()
        reply = OpenRouterLlm(settings).chat(
            [{"role": "user", "content": "Call the list_cards tool with no arguments."}], tools)
        ms = round((time.perf_counter() - t0) * 1000)
    except LlmError as e:
        report("FAIL", "openrouter", str(e)[:300])
        return
    report("PASS", "openrouter auth + model", f"{reply.model} in {ms} ms")
    if tools is None:
        report("WARN", "openrouter tool calling", "skipped (no MCP catalog)")
    elif any(c["function"]["name"] == "list_cards" for c in reply.tool_calls):
        report("PASS", "openrouter tool calling", f"model emitted list_cards call")
    else:
        report("FAIL", "openrouter tool calling", f"no tool call; finish={reply.finish_reason}")


def main() -> int:
    try:
        settings = load_settings()
        report("PASS", "config", f"model={settings.llm_model} guardrails={settings.guardrails} mcp={settings.mcp_url}")
    except ConfigError as e:
        report("FAIL", "config", str(e))
        return 1
    specs = asyncio.run(check_mcp(settings.mcp_url, settings.tool_timeout_s, build_limiter(settings)))
    check_llm(settings, specs)
    fails = sum(1 for s, *_ in results if s == "FAIL")
    warns = sum(1 for s, *_ in results if s == "WARN")
    print(f"\n{'HEALTHY' if not fails else 'UNHEALTHY'}: {fails} fail, {warns} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
