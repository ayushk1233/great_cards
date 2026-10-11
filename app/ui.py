"""Streamlit chat UI. Presentation only: every answer comes from orchestrator.run_turn().

    streamlit run app/ui.py

Each answer shows the exact tool calls (arguments + raw server JSON) and the guardrail
report, so any figure can be traced back to the tool output that produced it.
"""

import json
import sys
from pathlib import Path

# `streamlit run app/ui.py` puts app/ on sys.path, where app/mcp would shadow the MCP SDK's `mcp`
# package. Swap it for the project root so imports resolve as `app.*` plus the real SDK.
_APP_DIR = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _APP_DIR]
sys.path.insert(0, str(_APP_DIR.parent))

import streamlit as st

from app.agent import orchestrator
from app.config import ConfigError, load_settings

MODES = {
    "prompt": "Rules on (recommended): grounded-figure, monthly-field and fee rules; checks report only",
    "off": "Baseline: no extra rules; checks report only",
    "on": "Enforced: all rules, and an answer that fails a check is rewritten once, then replaced",
}
EXAMPLES = [
    "I spend ₹15,000 a month on Amazon and ₹3,000 on Swiggy. Which card?",
    "I'm salaried, ₹12 lakh a year, pincode 560001. Which cards can I get?",
    "Compare HDFC Millenia and SBI Cashback for ₹20,000 a month of online shopping.",
]
RAW_PREVIEW_CHARS = 20_000  # tool payloads can be 40k+ chars (the advisor playbook)


@st.cache_resource(show_spinner=False)
def get_agent(mode: str):
    # one agent per mode: keeps the tool catalog cache; the rate limiter state file is shared
    return orchestrator.build_agent(load_settings(), guardrails=mode)


def md(text: str) -> str:
    return text.replace("$", r"\$")  # Streamlit renders $...$ as LaTeX


def init_state() -> None:
    st.session_state.setdefault("messages", [])  # what the page shows: {"role", "content", "turn"}
    st.session_state.setdefault("history", [])   # what the model sees next turn (includes tool messages)
    st.session_state.setdefault("usage", {"turns": 0, "cost": 0.0, "tool_calls": 0})
    st.session_state.setdefault("server_info", {})


def reset() -> None:
    for key in ("messages", "history", "usage", "server_info"):
        st.session_state.pop(key, None)


def render_trace(turn: dict) -> None:
    trace = turn["trace"]
    sent = [t for t in trace if t["sent"]]
    label = f"Tool calls ({len(sent)} sent to the server)" if trace else "Tool calls (none)"
    with st.expander(label):
        if not trace:
            st.caption("No tool was called for this answer.")
        for i, t in enumerate(trace, 1):
            status = "ok" if t["ok"] else f"{t['error_kind']}"
            st.markdown(f"**{i}. `{t['tool']}`** · {status} · {t['latency_ms']} ms")
            st.caption("Arguments")
            st.code(json.dumps(t["arguments"], ensure_ascii=False, indent=2), language="json")
            st.caption("Raw result" if t["ok"] else "Error")
            body = t["raw"] or t["error_msg"] or ""
            if len(body) > RAW_PREVIEW_CHARS:
                body = body[:RAW_PREVIEW_CHARS] + f"\n… truncated for display ({len(t['raw']):,} chars in total)"
            st.code(body, language="json" if t["ok"] else None)


def render_checks(turn: dict, mode: str) -> None:
    v = turn["violations"]
    if turn["error"]:
        st.caption(f"⚠️ {turn['error']}")
        if turn["error_detail"]:
            with st.expander("Error detail"):
                st.code(turn["error_detail"])
        return
    if turn["fell_back"]:
        st.caption("🛑 Guardrail: the answer failed a check twice and was replaced with a safe reply.")
    elif turn["regenerated"]:
        st.caption("🔁 Guardrail: the first answer failed a check and was rewritten once.")
    if not v:
        st.caption("✅ Guardrail checks: no ungrounded ₹ figure, approval promise or tax advice detected.")
    else:
        enforced = mode == "on"
        st.caption(("🛑 Still flagged after rewrite:" if enforced else "⚠️ Flagged (report only):")
                   + " " + "; ".join(f"{x['rule']}: {x['snippet']}" for x in v))
    if turn["first_answer"]:
        with st.expander("Original answer before the guardrail rewrite"):
            st.markdown(md(turn["first_answer"]))
    if turn["hit_max_rounds"]:
        st.caption("ℹ️ The tool-call limit for this turn was reached; the answer uses what was gathered.")


def to_view(result) -> dict:
    """Plain dict for session state (TurnResult holds SDK-free dataclasses, but keep it simple)."""
    return {
        "trace": [{
            "tool": t.tool, "arguments": t.arguments, "ok": t.result.ok,
            "error_kind": t.result.error_kind, "error_msg": t.result.error_msg,
            "raw": t.result.raw_text, "latency_ms": t.result.latency_ms,
            "sent": t.result.error_kind not in orchestrator._NOT_SENT,
        } for t in result.trace],
        "violations": [{"rule": v.rule, "snippet": v.snippet} for v in result.validation.violations],
        "error": result.error, "error_detail": result.error_detail,
        "regenerated": result.regenerated, "fell_back": result.fell_back,
        "first_answer": result.first_answer, "hit_max_rounds": result.hit_max_rounds,
        "latency_ms": result.latency_ms, "cost": (result.usage or {}).get("cost") or 0.0,
    }


def sidebar(settings) -> str:
    with st.sidebar:
        st.header("Settings")
        # starts in "prompt", the measured fixed configuration; GUARDRAILS in .env is for the eval runner
        mode = st.radio("Guardrail mode", list(MODES), index=0, captions=list(MODES.values()))
        if st.button("New conversation", width="stretch"):
            reset()
            st.rerun()
        st.divider()
        u = st.session_state.usage
        st.caption(f"**Model:** {settings.llm_model}")
        st.caption(f"**Card data server:** {settings.mcp_url}")
        info = st.session_state.server_info
        if info:
            st.caption(f"**Server version:** {info.get('name', '')} {info.get('version', '')}".strip())
        st.caption(f"**This session:** {u['turns']} answers · {u['tool_calls']} tool calls · ${u['cost']:.4f}")
        st.caption(f"Tool calls per answer are capped at {settings.max_tool_calls_per_turn}, and requests to "
                   f"the card server are paced at {settings.mcp_max_requests} per {settings.mcp_window_s:.0f} s.")
    return mode


def main() -> None:
    st.set_page_config(page_title="Great.cards Card Advisor", page_icon="💳", layout="centered")
    try:
        settings = load_settings()
    except ConfigError as e:
        st.error(f"Configuration problem: {e}")
        st.stop()

    init_state()
    mode = sidebar(settings)

    st.title("💳 Card Advisor")
    st.caption("Answers come from Great.cards card tools. Figures are estimates, eligibility is indicative and "
               "the bank makes the final decision. This assistant doesn't give tax advice.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(md(msg["content"]))
            if msg.get("turn"):
                render_checks(msg["turn"], msg["mode"])
                render_trace(msg["turn"])

    prompt = st.chat_input("Ask about credit cards, e.g. your monthly spends")
    if not st.session_state.messages and not prompt:
        st.markdown("**Try asking:**")
        for i, example in enumerate(EXAMPLES):
            if st.button(example, key=f"example_{i}"):
                prompt = example
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(md(prompt))
    with st.chat_message("assistant"):
        with st.spinner("Checking the card tools…"):
            result = get_agent(mode).run_turn(st.session_state.history, prompt)
        turn = to_view(result)
        st.markdown(md(result.answer))
        render_checks(turn, mode)
        render_trace(turn)

    st.session_state.history = result.history
    st.session_state.messages.append({"role": "assistant", "content": result.answer, "turn": turn, "mode": mode})
    u = st.session_state.usage
    u["turns"] += 1
    u["cost"] += turn["cost"]
    u["tool_calls"] += sum(1 for t in turn["trace"] if t["sent"])
    if result.server_info:
        st.session_state.server_info = result.server_info
    st.rerun()  # refresh the sidebar counters


main()
