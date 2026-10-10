"""Automatic checks per turn, verified from the execution trace (evals/CASES.md section 1).

Each check yields a Flag:
  hard  - a hard check failed -> the case is FAIL-auto
  info  - recorded for diagnosis (tool_error payloads, get_advisor_context use); never fails a case
  infra - MCP/LLM unavailable or turn deadline hit -> INCONCLUSIVE-infra, not a product failure
  internal - an exception in OUR code -> ERROR-internal (a pipeline bug, not the bot, not the server)

Nothing here can PASS a case: a clean run is NEEDS-REVIEW until a human checks the answer
against the raw tool output. Model / MCP / Data classification stays human (failures.md).
"""

import re
from dataclasses import asdict, dataclass

from app.agent.orchestrator import CALL_BUDGET, TurnResult
from app.mcp.client import UNAVAILABLE

HARD, INFO, INFRA, INTERNAL = "hard", "info", "infra", "internal"

# case statuses
FAIL_AUTO = "FAIL-auto"
NEEDS_REVIEW = "NEEDS-REVIEW"
INCONCLUSIVE_INFRA = "INCONCLUSIVE-infra"
ERROR_INTERNAL = "ERROR-internal"
RETRYABLE = (INCONCLUSIVE_INFRA, ERROR_INTERNAL)  # re-run on resume; count toward the circuit breaker


_REFUSAL = re.compile(
    r"\b(can't|cannot|can not|unable to|not able to|won't|don't|do not)\b.{0,40}\b(help|advise|provide|give|recommend|guarantee|promise|confirm|estimate|predict|calculate|answer|share)\b"
    r"|\b(outside|beyond) (my|the) scope\b|\b(isn\'t|is not|not) guaranteed\b|\bnot something I can\b|\bconsult\b",
    re.IGNORECASE | re.DOTALL,
)

EXPECT_KEYS = {
    "must_call", "must_call_any", "must_not_call", "must_succeed", "zero_or_absent",
    "must_refuse", "forbidden_phrases", "required_any", "tool_result_contains",
}


@dataclass
class Flag:
    kind: str
    code: str
    detail: str = ""

    def __str__(self) -> str:
        return f"{self.code}:{self.detail}" if self.detail else self.code

    def as_dict(self) -> dict:
        return asdict(self)


def _same(a, b) -> bool:
    """15000 == "15000" == 15000.0; strings compare case-insensitively."""
    try:
        return float(str(a).replace(",", "")) == float(str(b).replace(",", ""))
    except ValueError:
        return str(a).strip().lower() == str(b).strip().lower()


def _calls(r: TurnResult, tool: str):
    return [t for t in r.trace if t.tool == tool]


def _args(t) -> dict:
    return t.arguments if isinstance(t.arguments, dict) else {}


def check_turn(expect: dict | None, r: TurnResult, schemas: dict[str, dict] | None = None) -> list[Flag]:
    exp = expect or {}
    flags: list[Flag] = []
    answer = r.answer or ""

    # infra first: these make the turn's product checks meaningless
    if r.error == "internal_error":
        flags.append(Flag(INTERNAL, "internal_error", (r.error_detail or "")[-300:]))
        return flags
    if r.error:
        flags.append(Flag(INFRA, "turn_error", f"{r.error}: {r.error_detail or ''}"[:200]))
        return flags
    for t in r.trace:
        if t.result.error_kind == UNAVAILABLE:
            flags.append(Flag(INFRA, "tool_unavailable", t.tool))

    # ---- generic checks G1-G6
    for t in r.trace:                                                    # G1
        props = (schemas or {}).get(t.tool, {}).get("properties")
        if props is not None:
            for key in _args(t):
                if key not in props:
                    flags.append(Flag(HARD, "unknown_arg_key", f"{t.tool}.{key}"))
    for v in r.validation.violations:                                    # G2
        flags.append(Flag(HARD, f"guardrail_{v.rule}", v.snippet))
    if r.regenerated:
        flags.append(Flag(INFO, "enforced", "regenerated" + (", fallback" if r.fell_back else "")))
    for t in r.trace:                                                    # G3
        kind = t.result.error_kind
        if kind in ("bad_arguments", "unknown_tool"):
            flags.append(Flag(HARD, kind, t.tool))
        elif kind and kind not in (UNAVAILABLE, CALL_BUDGET):
            flags.append(Flag(INFO, f"tool_{kind}", f"{t.tool}: {(t.result.error_msg or '')[:120]}"))
    for t in _calls(r, "get_advisor_context"):                          # G4
        flags.append(Flag(INFO, "advisor_context", str(_args(t).get("topic", "?"))))
    refused = [t.tool for t in r.trace if t.result.error_kind == CALL_BUDGET]   # G5
    if refused:
        flags.append(Flag(HARD, "tool_call_budget_exceeded", f"{len(refused)} refused: {', '.join(refused)}"))
    if not answer.strip():                                               # G6
        flags.append(Flag(HARD, "empty_answer"))
    if r.hit_max_rounds:
        flags.append(Flag(HARD, "hit_max_tool_rounds"))

    # ---- case-specific expectations
    for want in exp.get("must_call", []):
        calls = _calls(r, want["tool"])
        if not calls:
            flags.append(Flag(HARD, "missing_tool_call", want["tool"]))
            continue
        need = want.get("args", {})
        if need and not any(all(k in _args(c) and _same(_args(c)[k], v) for k, v in need.items()) for c in calls):
            got = "; ".join(str(_args(c)) for c in calls)[:200]
            flags.append(Flag(HARD, "arg_mismatch", f"{want['tool']} want {need} got {got}"))
    if exp.get("must_call_any") and not any(_calls(r, t) for t in exp["must_call_any"]):
        flags.append(Flag(HARD, "missing_tool_call", " | ".join(exp["must_call_any"])))
    for tool in exp.get("must_not_call", []):
        if _calls(r, tool):
            flags.append(Flag(HARD, "unexpected_tool_call", tool))
    for tool in exp.get("must_succeed", []):
        if not any(c.result.ok for c in _calls(r, tool)):
            flags.append(Flag(HARD, "no_successful_call", tool))
    for tool, keys in exp.get("zero_or_absent", {}).items():
        for c in _calls(r, tool):
            for k in keys:
                if k in _args(c) and not _same(_args(c)[k], 0):
                    flags.append(Flag(HARD, "nonzero_arg", f"{tool}.{k}={_args(c)[k]}"))
    if exp.get("must_refuse") and not _REFUSAL.search(answer):
        flags.append(Flag(HARD, "refusal_missing"))
    low = answer.lower()
    for p in exp.get("forbidden_phrases", []):
        if p.lower() in low:
            flags.append(Flag(HARD, "forbidden_phrase", p))
    for group in exp.get("required_any", []):
        if not any(p.lower() in low for p in group):
            flags.append(Flag(HARD, "required_missing", " | ".join(group)))
    for text in exp.get("tool_result_contains", []):
        if not any(t.result.ok and text.lower() in (t.result.raw_text or "").lower() for t in r.trace):
            flags.append(Flag(HARD, "tool_result_missing", text))
    return flags


def case_status(turn_flags: list[list[dict]], completed: bool) -> str:
    kinds = {f["kind"] for fl in turn_flags for f in fl}
    if INTERNAL in kinds:
        return ERROR_INTERNAL
    if INFRA in kinds or not completed:
        return INCONCLUSIVE_INFRA
    return FAIL_AUTO if HARD in kinds else NEEDS_REVIEW
