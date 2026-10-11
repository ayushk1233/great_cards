"""Streamlit chat UI. Presentation only: every answer comes from orchestrator.run_turn().

    streamlit run app/ui.py

Answers stream in as they are written (guardrail modes off and prompt; under "on" an answer is
shown only once it has passed the checks). Each answer lists the tools the server ran, with
their arguments, and the guardrail report.
"""

import base64
import html
import json
import queue
import sys
import threading
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
ASSETS = _APP_DIR / "assets"
AVATARS = {"user": str(ASSETS / "user.svg"), "assistant": str(ASSETS / "bot.svg")}
# st.html's sanitiser strips inline <svg>, so the logo goes in as an <img> data URI
LOGO_IMG = ('<img alt="" src="data:image/svg+xml;base64,'
            + base64.b64encode((ASSETS / "bot.svg").read_bytes()).decode() + '">')
EXAMPLES = [
    "I spend ₹15,000 a month on Amazon and ₹3,000 on Swiggy. Which card?",
    "I'm salaried, ₹12 lakh a year, pincode 560001. Which cards can I get?",
    "Compare HDFC Millenia and SBI Cashback for ₹20,000 a month of online shopping.",
]


@st.cache_resource(show_spinner=False)
def get_agent(mode: str):
    # one agent per mode: keeps the tool catalog cache; the rate limiter state file is shared
    return orchestrator.build_agent(load_settings(), guardrails=mode)


def md(text: str) -> str:
    return text.replace("$", r"\$")  # Streamlit renders $...$ as LaTeX


def inject_style() -> None:
    st.html(ASSETS / "style.css")  # style-only content: applied to the page, takes no space


def theme_toggle() -> None:
    """Sun/moon button at the top right; its script flips Streamlit's own light/dark setting."""
    st.html('<button id="ga-theme-toggle" type="button" data-mode="light">'
            '<span class="ga-sun">light_mode</span><span class="ga-moon">dark_mode</span></button>'
            f"<script>{(ASSETS / 'theme_toggle.js').read_text()}</script>",
            unsafe_allow_javascript=True)


def hero() -> None:
    # static markup only; nothing from the model or the server is ever rendered as HTML
    st.html(f"""<div class="ga-hero">{LOGO_IMG}<div>
      <h1>Card Advisor</h1>
      <p>Find the Indian credit card that fits how you spend.</p>
      <div class="ga-pills"><span class="ga-pill">Live Great.cards card data</span>
        <span class="ga-pill">Tool calls shown under every answer</span>
        <span class="ga-pill">Guardrail check on every answer</span></div>
    </div></div>""")


def working(tools: list[str]) -> str:
    """Animated 'working' line: bouncing dots, then a chip per tool call (the last one still running)."""
    chips = "".join(f'<span class="ga-chip {"live" if i == len(tools) - 1 else "done"}">{html.escape(t)}</span>'
                    for i, t in enumerate(tools))
    label = "Asking the card server" if tools else "Checking the card tools"
    return f'<div class="ga-working"><span class="ga-dots"><i></i><i></i><i></i></span><span>{label}…</span>{chips}</div>'


def init_state() -> None:
    st.session_state.setdefault("messages", [])  # what the page shows: {"role", "content", "turn"}
    st.session_state.setdefault("history", [])   # what the model sees next turn (includes tool messages)
    st.session_state.setdefault("usage", {"turns": 0, "cost": 0.0, "tool_calls": 0})
    st.session_state.setdefault("server_info", {})
    st.session_state.setdefault("pending", None)  # {"prompt", "mode"} while an answer is being generated


def reset() -> None:
    for key in ("messages", "history", "usage", "server_info"):
        st.session_state.pop(key, None)


def render_trace(turn: dict) -> None:
    """Only the calls the server actually ran: name, status, time and arguments (no raw JSON)."""
    sent = [t for t in turn["trace"] if t["sent"]]
    not_sent = len(turn["trace"]) - len(sent)
    label = f"Tool calls ({len(sent)} sent to the server)" if sent else "Tool calls (none)"
    with st.expander(label, icon=":material/build:"):
        if not sent:
            st.caption("No tool was called for this answer.")
        for i, t in enumerate(sent, 1):
            status = "ok" if t["ok"] else f"{t['error_kind']}"
            st.markdown(f"**{i}. `{t['tool']}`** · {status} · {t['latency_ms']} ms")
            st.code(json.dumps(t["arguments"], ensure_ascii=False), language="json")
            if not t["ok"] and t["error_msg"]:
                st.caption(t["error_msg"][:300])
        if not_sent:
            st.caption(f"{not_sent} more call(s) were not sent: over the per-answer limit or invalid.")


def render_checks(turn: dict, mode: str) -> None:
    """One row of status badges, then the detail in a caption."""
    v = turn["violations"]
    if turn["error"]:
        st.markdown(f":red-badge[:material/error: {turn['error']}]")
        if turn["error_detail"]:
            with st.expander("Error detail"):
                st.code(turn["error_detail"])
        return
    badges = []
    if turn["fell_back"]:
        badges.append(":red-badge[:material/block: Replaced with a safe reply]")
    elif turn["regenerated"]:
        badges.append(":blue-badge[:material/autorenew: Rewritten once]")
    if not v:
        badges.append(":green-badge[:material/verified: Checks passed]")
    elif mode == "on":
        badges.append(":red-badge[:material/gpp_bad: Still flagged after rewrite]")
    else:
        badges.append(":orange-badge[:material/warning: Flagged (report only)]")
    st.markdown(" ".join(badges))
    if turn["fell_back"]:
        st.caption("The answer failed a check twice, so a safe reply was shown instead.")
    elif turn["regenerated"]:
        st.caption("The first answer failed a check and was rewritten once.")
    if not v:
        st.caption("Guardrail checks: no ungrounded ₹ figure, approval promise or tax advice detected.")
    else:
        st.caption(md("; ".join(f"{x['rule']}: {x['snippet']}" for x in v)))
    if turn["first_answer"]:
        with st.expander("Original answer before the guardrail rewrite"):
            st.markdown(md(turn["first_answer"]))
    if turn["hit_max_rounds"]:
        st.caption(":material/info: The tool-call limit for this turn was reached; the answer uses what was gathered.")


def to_view(result) -> dict:
    """Plain dict for session state (TurnResult holds SDK-free dataclasses, but keep it simple)."""
    return {
        "trace": [{
            "tool": t.tool, "arguments": t.arguments, "ok": t.result.ok,
            "error_kind": t.result.error_kind, "error_msg": t.result.error_msg,
            "latency_ms": t.result.latency_ms,
            "sent": t.result.error_kind not in orchestrator._NOT_SENT,
        } for t in result.trace],
        "violations": [{"rule": v.rule, "snippet": v.snippet} for v in result.validation.violations],
        "error": result.error, "error_detail": result.error_detail,
        "regenerated": result.regenerated, "fell_back": result.fell_back,
        "first_answer": result.first_answer, "hit_max_rounds": result.hit_max_rounds,
        "latency_ms": result.latency_ms, "cost": (result.usage or {}).get("cost") or 0.0,
    }


def stream_turn(agent, history: list[dict], prompt: str):
    """Run the turn in a worker thread and draw its events as they arrive. Only this (script)
    thread touches Streamlit; the worker just puts events on a queue."""
    events: queue.Queue = queue.Queue()
    out: dict = {}

    def work():
        try:
            out["result"] = agent.run_turn(history, prompt, on_event=events.put)
        except BaseException as e:  # re-raised below, on the script thread
            out["error"] = e
        finally:
            events.put(None)

    threading.Thread(target=work, daemon=True).start()
    status, body = st.empty(), st.empty()
    status.html(working([]))
    text, tools, live = "", [], None
    while (ev := events.get()) is not None:
        if ev[0] == "tool_call":
            tools.append(ev[1])
            status.html(working(tools))
        elif ev[0] == "text":
            text += ev[1]
            status.empty()
            if live is None:  # keyed container: style.css draws the blinking caret inside it
                live = body.container(key="ga-live").empty()
            live.markdown(md(text))
        elif ev[0] == "discard" and live is not None:
            text = ""
            live.empty()
    if "error" in out:
        raise out["error"]
    status.empty()
    body.markdown(md(out["result"].answer))  # the final answer replaces the streamed draft (and its caret)
    return out["result"]


def sidebar(settings, busy: bool) -> str:
    with st.sidebar:
        st.html(f'<div class="ga-brand">{LOGO_IMG}<div><b>Great.cards</b><span>Card Advisor</span></div></div>')
        st.subheader(":material/tune: Settings")
        # starts in "prompt", the measured fixed configuration; GUARDRAILS in .env is for the eval runner
        mode = st.radio("Guardrail mode", list(MODES), index=0, captions=list(MODES.values()), disabled=busy)
        if st.button("New conversation", icon=":material/add_comment:", width="stretch", disabled=busy):
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

    inject_style()
    theme_toggle()
    init_state()
    # A question is answered in two runs: the run that receives it stores it and reruns at once, and the
    # next run draws every widget disabled and then answers. Clicking a widget mid-answer would stop the
    # run and lose the answer, so nothing on the page is clickable until it's done.
    pending = st.session_state.pending
    busy = pending is not None
    mode = sidebar(settings, busy)

    hero()
    st.caption("Answers come from Great.cards card tools. Figures are estimates, eligibility is indicative and "
               "the bank makes the final decision. This assistant doesn't give tax advice.")
    # One fixed slot for the examples, so they are replaced at once instead of lingering faded (and
    # clickable) while the next run is still going
    examples = st.empty()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
            st.markdown(md(msg["content"]))
            if msg.get("turn"):
                render_checks(msg["turn"], msg["mode"])
                render_trace(msg["turn"])

    prompt = st.chat_input("Ask about credit cards, e.g. your monthly spends", disabled=busy)
    if not busy and not st.session_state.messages and not prompt:
        with examples.container(border=True, key="ga-examples"):
            st.markdown("**Try asking**")
            for i, example in enumerate(EXAMPLES):
                if st.button(example, key=f"example_{i}", icon=":material/chat_bubble_outline:", width="stretch"):
                    prompt = example
    if prompt and not busy:
        examples.empty()
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending = {"prompt": prompt, "mode": mode}
        st.rerun()
    if not busy:
        return

    prompt, mode = pending["prompt"], pending["mode"]
    try:
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            result = stream_turn(get_agent(mode), st.session_state.history, prompt)
            turn = to_view(result)
            render_checks(turn, mode)
            render_trace(turn)
    finally:
        st.session_state.pending = None  # never leave the page locked, even if the turn raised

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
