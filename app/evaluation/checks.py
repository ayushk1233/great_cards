"""Automatic flags per question. These only *flag*; classifying a failure as
Model / MCP tool / Data stays a human judgement recorded in failures.md."""

import re

from app.agent.orchestrator import TurnResult

_REFUSAL = re.compile(
    r"\b(can't|cannot|can not|unable to|not able to|won't|don't|do not)\b.{0,40}\b(help|advise|provide|give|recommend|guarantee|promise|confirm|estimate|predict|calculate|answer|share)\b"
    r"|\b(outside|beyond) (my|the) scope\b|\b(isn\'t|is not|not) guaranteed\b|\bnot something I can\b|\bconsult\b",
    re.IGNORECASE | re.DOTALL,
)


def run_checks(q: dict, r: TurnResult) -> list[str]:
    exp = q.get("expectations", {}) or {}
    called = [t.tool for t in r.trace]
    flags = []
    if r.error:
        flags.append(f"error:{r.error}")
    for v in r.validation.violations:
        flags.append(f"guardrail:{v.rule}:{v.snippet}")
    if r.regenerated:
        flags.append("enforced:regenerated" + (":fallback" if r.fell_back else ""))
    for t in r.trace:
        if not t.result.ok:
            flags.append(f"tool_error:{t.tool}:{t.result.error_kind}")
    for tool in exp.get("must_call_tools", []):
        if tool not in called:
            flags.append(f"missing_tool_call:{tool}")
    for tool in exp.get("must_not_call_tools", []):
        if tool in called:
            flags.append(f"unexpected_tool_call:{tool}")
    if exp.get("must_refuse") and not _REFUSAL.search(r.answer):
        flags.append("expected_refusal_missing")
    for p in exp.get("forbidden_phrases", []):
        if p.lower() in r.answer.lower():
            flags.append(f"forbidden_phrase:{p}")
    for p in exp.get("required_phrases", []):
        if p.lower() not in r.answer.lower():
            flags.append(f"required_phrase_missing:{p}")
    if r.hit_max_rounds:
        flags.append("hit_max_tool_rounds")
    return flags
