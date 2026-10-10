"""One chat turn: LLM <-> MCP tool loop, then validation.

run_turn(history, user_msg) -> TurnResult. history holds prior role dicts (including tool
messages), so follow-ups can reuse earlier tool results without re-calling the server.
"""

import asyncio
import json
import threading
import time
import traceback
from dataclasses import dataclass, field, replace
from typing import Any, Callable

from app.agent import prompts
from app.agent.llm import LlmError, LlmReply
from app.agent.validation import ValidationReport, validate
from app.config import Settings, build_limiter
from app.mcp.client import McpSession, ToolResult

CALL_BUDGET = "call_budget"  # error_kind for calls refused by the per-turn budget (never sent)
_NOT_SENT = {CALL_BUDGET, "bad_arguments", "unknown_tool"}  # trace entries that never reached the server
from app.mcp.tools import ALLOWLIST, MissingToolError, build_tool_specs


@dataclass
class TraceEntry:
    round: int
    tool: str
    arguments: Any            # parsed args (or the raw string if unparseable)
    result: ToolResult


@dataclass
class TurnResult:
    answer: str
    trace: list[TraceEntry] = field(default_factory=list)
    validation: ValidationReport = field(default_factory=ValidationReport)
    error: str | None = None  # None | mcp_unavailable | catalog | llm_error | turn_timeout | internal_error
    error_detail: str | None = None
    history: list[dict] = field(default_factory=list)   # history to pass into the next turn
    rounds: int = 0
    hit_max_rounds: bool = False
    regenerated: bool = False             # guardrails=on: answer was rewritten once
    fell_back: bool = False               # guardrails=on: still violating -> fallback text
    first_answer: str | None = None       # pre-regeneration answer, kept as evidence
    first_validation: ValidationReport | None = None
    server_info: dict = field(default_factory=dict)
    latency_ms: int = 0
    usage: dict = field(default_factory=dict)  # summed over every LLM call this turn


class Agent:
    def __init__(self, settings: Settings, llm, session_factory: Callable | None = None, limiter=None):
        self.settings = settings
        self.llm = llm
        self.limiter = limiter
        self.session_factory = session_factory or (
            lambda: McpSession(settings.mcp_url, settings.tool_timeout_s, limiter=self.limiter))
        self._catalog: list[dict] | None = None   # raw tools/list, cached for catalog_ttl_s
        self._catalog_at = 0.0
        self._catalog_lock = threading.Lock()

    def prime_catalog(self, tools: list[dict]) -> None:
        """Seed the tools/list cache (e.g. from the runner's header fetch)."""
        with self._catalog_lock:
            self._catalog, self._catalog_at = tools, time.monotonic()

    def tool_schemas(self) -> dict[str, dict]:
        """inputSchema per allowlisted tool from the cached catalog ({} if not fetched yet)."""
        with self._catalog_lock:
            tools = self._catalog or []
        return {t["name"]: t.get("inputSchema", {}) for t in tools if t.get("name") in ALLOWLIST}

    async def _tools(self, mcp) -> list[dict]:
        with self._catalog_lock:
            fresh = self._catalog is not None and time.monotonic() - self._catalog_at < self.settings.catalog_ttl_s
            if fresh:
                return self._catalog
        tools = await mcp.list_tools()
        self.prime_catalog(tools)
        return tools

    def run_turn(self, history: list[dict], user_msg: str) -> TurnResult:
        return asyncio.run(self.arun_turn(history, user_msg))

    async def _chat(self, messages, tools=None) -> LlmReply:
        # the SDK call is blocking; keep the MCP session's event loop free while we wait
        reply = await asyncio.to_thread(self.llm.chat, messages, tools)
        u = reply.usage or {}
        self._usage["llm_calls"] += 1
        for k in ("prompt_tokens", "completion_tokens", "cost"):
            self._usage[k] += u.get(k) or 0
        return reply

    async def arun_turn(self, history: list[dict], user_msg: str) -> TurnResult:
        started = time.perf_counter()
        self._usage = {"llm_calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}
        trace: list[TraceEntry] = []  # outside _turn so a timed-out turn still reports what ran
        try:
            res = await asyncio.wait_for(self._turn(history, user_msg, trace), self.settings.turn_deadline_s)
        except asyncio.TimeoutError:
            res = TurnResult(prompts.TURN_TIMEOUT, trace=list(trace), error="turn_timeout",
                             error_detail=f"turn exceeded {self.settings.turn_deadline_s:.0f} s", history=list(history))
        res.latency_ms = round((time.perf_counter() - started) * 1000)
        res.usage = dict(self._usage)
        return res

    async def _turn(self, history: list[dict], user_msg: str, trace: list[TraceEntry]) -> TurnResult:
        s = self.settings
        convo = list(history) + [{"role": "user", "content": user_msg}]
        system = {"role": "system", "content": prompts.system_prompt(s.guardrails)}

        # 1. connect + catalog: failures here really are the MCP service
        session = self.session_factory()
        try:
            mcp = await session.__aenter__()
        except Exception as e:  # network, 429 on initialize, TLS, ...
            return TurnResult(prompts.SERVICE_UNAVAILABLE, error="mcp_unavailable",
                              error_detail=f"connect: {type(e).__name__}: {e}", history=list(history))
        try:
            try:
                specs = build_tool_specs(await self._tools(mcp))
            except MissingToolError as e:
                with self._catalog_lock:
                    self._catalog = None  # don't keep serving a catalog that failed the check
                return TurnResult(prompts.SERVICE_UNAVAILABLE, error="catalog", error_detail=str(e),
                                  history=list(history))
            except Exception as e:
                return TurnResult(prompts.SERVICE_UNAVAILABLE, error="mcp_unavailable",
                                  error_detail=f"tools/list: {type(e).__name__}: {e}", history=list(history))

            # 2. the tool loop: call_tool never raises (it returns ToolResult), so anything that
            # escapes here is the LLM or a bug in our code, never "the server is down"
            try:
                result = await self._loop(mcp, system, convo, specs, trace)
            except LlmError as e:
                return TurnResult(prompts.LLM_UNAVAILABLE, trace=list(trace), error="llm_error",
                                  error_detail=str(e), history=list(history))
            except Exception as e:
                return TurnResult(prompts.INTERNAL_ERROR, trace=list(trace), error="internal_error",
                                  error_detail="".join(traceback.format_exception(e))[-2000:],
                                  history=list(history))
            result.server_info = dict(getattr(mcp, "server_info", {}) or {})
            return result
        finally:
            try:
                await session.__aexit__(None, None, None)
            except Exception:
                pass

    async def _loop(self, mcp, system, convo, specs, trace) -> TurnResult:
        s = self.settings
        rounds, hit_max = 0, False
        while True:
            if rounds >= s.max_tool_rounds:
                hit_max = True
                reply = await self._chat([system] + convo + [{"role": "user", "content": prompts.MAX_ROUNDS_NOTE}])
                break
            reply = await self._chat([system] + convo, specs)
            if not reply.tool_calls:
                break
            rounds += 1
            convo.append(reply.as_message())
            for call in reply.tool_calls:  # sequential on purpose: production server, no parallel load
                if sum(1 for t in trace if t.result.error_kind not in _NOT_SENT) >= s.max_tool_calls_per_turn:
                    convo.append(self._refuse_call(call, rounds, trace))
                else:
                    convo.append(await self._run_call(mcp, call, rounds, trace))

        answer = reply.text.strip()
        convo.append({"role": "assistant", "content": answer})
        result = TurnResult(answer, trace=trace, rounds=rounds, hit_max_rounds=hit_max, history=convo)
        result.validation = self._validate(answer, trace, convo)

        if s.guardrails == "on" and not result.validation.ok:
            await self._enforce(result, system, convo)
        return result

    async def _run_call(self, mcp, call: dict, rnd: int, trace: list[TraceEntry]) -> dict:
        name = call["function"]["name"]
        raw_args = call["function"].get("arguments") or "{}"
        try:
            args = json.loads(raw_args)
            if not isinstance(args, dict):
                raise ValueError("arguments must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            tr = ToolResult(ok=False, error_kind="bad_arguments", error_msg=f"could not parse tool arguments: {e}")
            trace.append(TraceEntry(rnd, name, raw_args, tr))
            return {"role": "tool", "tool_call_id": call["id"], "content": tr.for_model()}
        if name not in ALLOWLIST:
            tr = ToolResult(ok=False, error_kind="unknown_tool", error_msg=f"tool {name!r} is not available")
        else:
            tr = await mcp.call_tool(name, args)
        trace.append(TraceEntry(rnd, name, args, tr))
        return {"role": "tool", "tool_call_id": call["id"], "content": tr.for_model()}

    def _refuse_call(self, call: dict, rnd: int, trace: list[TraceEntry]) -> dict:
        """Over the per-turn budget: answer the tool_call_id without touching the server."""
        name = call["function"]["name"]
        try:
            args = json.loads(call["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            args = call["function"].get("arguments")
        tr = ToolResult(ok=False, error_kind=CALL_BUDGET,
                        error_msg=prompts.CALL_BUDGET_NOTE.format(n=self.settings.max_tool_calls_per_turn))
        trace.append(TraceEntry(rnd, name, args, tr))
        return {"role": "tool", "tool_call_id": call["id"], "content": tr.for_model()}

    @staticmethod
    def _validate(answer: str, trace: list[TraceEntry], convo: list[dict]) -> ValidationReport:
        # tool payloads from this turn AND earlier turns (follow-ups may cite older results)
        payloads = [m["content"] for m in convo if m.get("role") == "tool"]
        payloads += [t.result.data if t.result.ok else t.result.raw_text for t in trace]
        users = [m["content"] for m in convo if m.get("role") == "user" and isinstance(m.get("content"), str)]
        return validate(answer, payloads, users)

    async def _enforce(self, result: TurnResult, system: dict, convo: list[dict]) -> None:
        """GUARDRAILS=on: one rewrite with the violations listed, then a safe fallback."""
        result.first_answer, result.first_validation = result.answer, result.validation
        feedback = prompts.VALIDATOR_FEEDBACK.format(
            violations="\n".join(f"- {v.rule}: {v.snippet}" for v in result.validation.violations))
        reply = await self._chat([system] + convo + [{"role": "user", "content": feedback}])
        result.regenerated = True
        answer = reply.text.strip()
        report = self._validate(answer, result.trace, convo)
        if not report.ok:
            answer, result.fell_back = prompts.FALLBACK_ANSWER, True
            report = self._validate(answer, result.trace, convo)
        result.answer, result.validation = answer, report
        convo[-1] = {"role": "assistant", "content": answer}  # feedback exchange stays out of history


def build_agent(settings: Settings, guardrails: str | None = None, limiter=None) -> Agent:
    from app.agent.llm import OpenRouterLlm

    if guardrails:
        settings = replace(settings, guardrails=guardrails)
    return Agent(settings, OpenRouterLlm(settings), limiter=limiter or build_limiter(settings))
