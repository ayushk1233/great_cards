"""Discovery client for the Great.cards MCP server.

Connects over Streamable HTTP with the official MCP SDK, runs named scenario
groups sequentially, and writes every request/response verbatim to
discovery/raw/ so each finding can cite its evidence.

Usage:
    python discovery/probe.py --list              # tools/prompts catalog only
    python discovery/probe.py context recommend   # run scenario groups
"""

import argparse
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from scenarios import SCENARIOS

SERVER_URL = "https://bk-api.bankkaro.com/mcp"
HERE = Path(__file__).parent
RAW_DIR = HERE / "raw"
CALL_LOG = HERE / "call_log.jsonl"


def _dump(obj):
    return obj.model_dump(mode="json", by_alias=True, exclude_none=True) if hasattr(obj, "model_dump") else obj


def _parse_text(result):
    """Return the parsed JSON of each text content item (or the raw text if not JSON)."""
    parsed = []
    for item in result.get("content", []):
        text = item.get("text")
        if text is None:
            continue
        try:
            parsed.append(json.loads(text))
        except json.JSONDecodeError:
            parsed.append(text)
    return parsed


async def catalog(session: ClientSession, init):
    tools = _dump(await session.list_tools())
    prompts = _dump(await session.list_prompts())
    prompt_bodies = {}
    for p in prompts.get("prompts", []):
        try:
            prompt_bodies[p["name"]] = _dump(await session.get_prompt(p["name"]))
        except Exception as e:  # record, don't hide
            prompt_bodies[p["name"]] = {"error": repr(e)}

    (HERE / "tools.json").write_text(json.dumps(tools, indent=2, ensure_ascii=False))
    (HERE / "prompts.json").write_text(
        json.dumps({"list": prompts, "bodies": prompt_bodies}, indent=2, ensure_ascii=False)
    )
    (HERE / "server_info.json").write_text(json.dumps(_dump(init), indent=2, ensure_ascii=False))

    lines = [f"# Tool catalog (verbatim from tools/list)\n",
             f"Server: `{SERVER_URL}` — captured {datetime.now(timezone.utc).isoformat()}\n",
             f"{len(tools['tools'])} tools.\n"]
    for t in tools["tools"]:
        schema = t.get("inputSchema", {})
        lines.append(f"\n## `{t['name']}`\n")
        lines.append(f"- Required: `{schema.get('required', [])}`")
        lines.append(f"- outputSchema: {'yes' if t.get('outputSchema') else 'no'} · annotations: {t.get('annotations')}\n")
        lines.append("### Description\n\n```text\n" + (t.get("description") or "") + "\n```\n")
        lines.append("### Input schema\n\n```json\n" + json.dumps(schema, indent=2, ensure_ascii=False) + "\n```\n")
    (HERE / "tool_catalog.md").write_text("\n".join(lines))
    print(f"catalog: {len(tools['tools'])} tools, {len(prompts.get('prompts', []))} prompts")


async def run_scenario(session: ClientSession, group: str, sc: dict):
    started = time.perf_counter()
    error = None
    try:
        result = _dump(await session.call_tool(sc["tool"], sc["args"]))
    except Exception as e:
        result = None
        error = repr(e)
    latency_ms = round((time.perf_counter() - started) * 1000)

    record = {
        "id": sc["id"],
        "group": group,
        "purpose": sc.get("purpose", ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request": {"tool": sc["tool"], "arguments": sc["args"]},
        "latency_ms": latency_ms,
        "client_error": error,
        "is_error": (result or {}).get("isError"),
        "raw_result": result,
        "parsed_content": _parse_text(result) if result else None,
    }
    (RAW_DIR / f"{group}__{sc['id']}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False))
    with CALL_LOG.open("a") as f:
        f.write(json.dumps({k: record[k] for k in ("id", "group", "timestamp", "latency_ms", "is_error", "client_error")}) + "\n")
    status = "CLIENT_ERR" if error else ("isError" if record["is_error"] else "ok")
    print(f"  {group}/{sc['id']:<40} {status:<10} {latency_ms} ms")


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("groups", nargs="*", help=f"scenario groups: {', '.join(SCENARIOS)}")
    ap.add_argument("--list", action="store_true", help="capture tools/prompts catalog")
    args = ap.parse_args()
    RAW_DIR.mkdir(exist_ok=True)

    async with streamable_http_client(SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            print(f"connected: {init.server_info.name} v{init.server_info.version} (protocol {init.protocol_version})")
            if args.list:
                await catalog(session, init)
            for group in args.groups:
                print(f"[{group}]")
                for sc in SCENARIOS[group]:
                    await run_scenario(session, group, sc)  # sequential on purpose: no load


if __name__ == "__main__":
    asyncio.run(main())
