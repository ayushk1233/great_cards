"""Streamlit UI, driven headlessly with AppTest and a fake agent (no network, no API key used)."""

from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from app.agent import orchestrator
from app.agent.llm import LlmReply
from app.agent.orchestrator import Agent
from app.mcp.client import normalize
from tests.test_orchestrator import FakeLlm, FakeMcp, call, settings

UI = str(Path(__file__).resolve().parent.parent / "app" / "ui.py")


@pytest.fixture
def fake_agent(monkeypatch, live_catalog, raw):
    """Patch build_agent so the page talks to a scripted LLM and a recorded MCP result."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    st.cache_resource.clear()
    amazon = normalize(raw("recommend__amazon_15k")["raw_result"])
    built = {}

    def install(*replies):
        mcp = FakeMcp(live_catalog, {"recommend_cards": amazon})

        def build(s, guardrails=None, limiter=None):
            built["mode"] = guardrails
            return Agent(settings(guardrails or "off"), FakeLlm(list(replies)), session_factory=lambda: mcp)

        monkeypatch.setattr(orchestrator, "build_agent", build)
        return mcp

    yield install, built
    st.cache_resource.clear()


def all_text(at: AppTest) -> str:
    parts = [m.value for m in at.markdown] + [c.value for c in at.caption] + [c.value for c in at.code]
    return "\n".join(str(p) for p in parts)


def test_empty_state_renders(fake_agent):
    fake_agent[0]()
    at = AppTest.from_file(UI, default_timeout=10).run()
    assert not at.exception
    assert at.title[0].value == "💳 Card Advisor"
    assert at.sidebar.radio[0].value == "prompt"  # starts in the measured fixed configuration
    assert len(at.button) >= 4  # 3 examples + new conversation


def test_turn_shows_answer_trace_and_checks(fake_agent):
    install, built = fake_agent
    mcp = install(LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]),
                  LlmReply("HDFC Millenia: ₹9,000 a year, joining fee ₹1,180."))
    at = AppTest.from_file(UI, default_timeout=10).run()
    at.chat_input[0].set_value("I spend 15k a month on Amazon").run()
    assert not at.exception
    assert mcp.calls == [("recommend_cards", {"amazon_spends": 15000})]
    assert built["mode"] == "prompt"
    text = all_text(at)
    assert "HDFC Millenia: ₹9,000 a year" in text
    assert "✅ Guardrail checks" in text
    assert '{"amazon_spends": 15000}' in text           # arguments shown verbatim
    assert len(at.code) == 1                             # one block per call (its arguments), no raw JSON
    assert "▌" not in text                               # the streaming cursor is gone once done
    assert at.expander[0].label == "Tool calls (1 sent to the server)"
    assert "1 answers · 1 tool calls" in text            # sidebar counters updated


def test_flagged_figure_is_reported_not_hidden(fake_agent):
    install, _ = fake_agent
    install(LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]),
            LlmReply("You'd save ₹12,345 a year."))
    at = AppTest.from_file(UI, default_timeout=10).run()
    at.chat_input[0].set_value("I spend 15k a month on Amazon").run()
    text = all_text(at)
    assert "You'd save ₹12,345 a year." in text           # prompt mode: report only, answer kept
    assert "⚠️ Flagged (report only): unreturned_rupee" in text


def test_example_button_starts_a_turn(fake_agent):
    install, _ = fake_agent
    install(LlmReply("Tell me your monthly spends."))
    at = AppTest.from_file(UI, default_timeout=10).run()
    at.button(key="example_0").click().run()
    assert not at.exception
    assert "Tell me your monthly spends." in all_text(at)
    assert at.expander[0].label == "Tool calls (none)"


def test_new_conversation_clears_chat(fake_agent):
    install, _ = fake_agent
    install(LlmReply("First answer."))
    at = AppTest.from_file(UI, default_timeout=10).run()
    at.chat_input[0].set_value("hi").run()
    assert "First answer." in all_text(at)
    at.sidebar.button[0].click().run()
    assert "First answer." not in all_text(at)
    assert at.session_state.messages == []


def test_missing_key_shows_config_error(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    at = AppTest.from_file(UI, default_timeout=10).run()
    assert at.error and "OPENROUTER_API_KEY is missing" in at.error[0].value


def test_dollar_signs_do_not_render_as_latex(fake_agent):
    install, _ = fake_agent
    install(LlmReply("That costs $0.02 and $5 in fees."))
    at = AppTest.from_file(UI, default_timeout=10).run()
    at.chat_input[0].set_value("hi").run()
    assert r"That costs \$0.02 and \$5 in fees." in [m.value for m in at.markdown]


def test_script_imports_real_mcp_sdk_when_run_from_app_dir():
    """`streamlit run app/ui.py` puts app/ first on sys.path, where app/mcp shadows the SDK. Running
    the file directly reproduces that path layout (bare mode: no server, no network, no prompt)."""
    import os
    import subprocess
    import sys
    env = {**os.environ, "OPENROUTER_API_KEY": "test-key"}
    r = subprocess.run([sys.executable, UI], capture_output=True, text=True, timeout=60, env=env,
                       cwd=Path(UI).parent)
    assert r.returncode == 0, r.stderr[-2000:]
    assert "ImportError" not in r.stderr


def test_calls_not_sent_are_left_out_of_the_panel(fake_agent):
    install, _ = fake_agent
    mcp = install(LlmReply("", [call("recommend_cards", {"amazon_spends": 15000}), call("not_a_tool", {}, "c2")]),
                  LlmReply("HDFC Millenia: ₹9,000 a year."))
    at = AppTest.from_file(UI, default_timeout=10).run()
    at.chat_input[0].set_value("I spend 15k a month on Amazon").run()
    assert not at.exception
    assert mcp.calls == [("recommend_cards", {"amazon_spends": 15000})]
    assert at.expander[0].label == "Tool calls (1 sent to the server)"
    text = all_text(at)
    assert "not_a_tool" not in text and "1 more call(s) were not sent" in text


def test_page_is_locked_while_an_answer_is_generated(monkeypatch):
    """A turn that raises freezes the run mid-answer, so the page can be inspected in its busy state."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    st.cache_resource.clear()

    class Exploding:
        def run_turn(self, history, prompt, on_event=None):
            raise RuntimeError("stop mid-answer")

    monkeypatch.setattr(orchestrator, "build_agent", lambda s, guardrails=None, limiter=None: Exploding())
    at = AppTest.from_file(UI, default_timeout=10).run()
    at.chat_input[0].set_value("hi").run()

    assert at.exception and "stop mid-answer" in at.exception[0].message
    assert at.chat_input[0].proto.disabled
    assert at.sidebar.radio[0].proto.disabled
    assert at.sidebar.button[0].proto.disabled                 # New conversation
    assert not [b for b in at.button if b.key and b.key.startswith("example_")]
    assert [m.value for m in at.markdown if m.value == "hi"]     # the question stays on the page

    at.run()                                                     # the failed turn doesn't leave it locked
    assert not at.chat_input[0].proto.disabled and not at.sidebar.radio[0].proto.disabled
    st.cache_resource.clear()
