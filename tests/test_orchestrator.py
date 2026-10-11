"""Tool loop + guardrail behaviour with a scripted fake LLM and fake MCP (no network)."""

import json

import pytest

from app.agent import prompts
from app.agent.llm import LlmError, LlmReply
from app.agent.orchestrator import Agent
from app.config import Settings
from app.mcp.client import UNAVAILABLE, ToolResult, normalize


def settings(guardrails="off", max_rounds=6):
    return Settings("test-key", "fake/model", "http://unused", guardrails, max_tool_rounds=max_rounds)


def call(name, args, cid="c1"):
    raw = args if isinstance(args, str) else json.dumps(args)
    return {"id": cid, "type": "function", "function": {"name": name, "arguments": raw}}


class FakeLlm:
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def chat(self, messages, tools=None, on_text=None):
        self.seen.append({"messages": messages, "tools": tools, "streamed": on_text is not None})
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        if on_text and r.text:  # stream word by word, like the real client's text chunks
            for i, piece in enumerate(r.text.split(" ")):
                on_text(piece if i == 0 else " " + piece)
        return r


class FakeMcp:
    def __init__(self, catalog, results=None):
        self.catalog, self.results, self.calls = catalog, results or {}, []
        self.server_info = {"name": "great-cards", "version": "test"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return None

    async def list_tools(self):
        return self.catalog

    async def call_tool(self, name, args):
        self.calls.append((name, args))
        return self.results.get(name, ToolResult(ok=True, data={}))


@pytest.fixture
def amazon_result(raw):
    return normalize(raw("recommend__amazon_15k")["raw_result"])


def make(llm, mcp, **kw):
    return Agent(settings(**kw), llm, session_factory=lambda: mcp)


def test_tool_loop_happy_path(live_catalog, amazon_result):
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    llm = FakeLlm([LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]),
                   LlmReply("HDFC Millenia: ₹9,000 a year, joining fee ₹1,180.")])
    r = make(llm, mcp).run_turn([], "I spend 15k a month on Amazon")
    assert r.error is None and r.validation.ok
    assert mcp.calls == [("recommend_cards", {"amazon_spends": 15000})]
    assert [t.tool for t in r.trace] == ["recommend_cards"] and r.rounds == 1
    assert len(llm.seen[0]["tools"]) == 7
    roles = [m["role"] for m in r.history]
    assert roles == ["user", "assistant", "tool", "assistant"]


def test_tool_error_is_fed_back_not_raised(live_catalog, raw):
    bad = normalize(raw("edge__details_bad_alias")["raw_result"])
    mcp = FakeMcp(live_catalog, {"get_card_details": bad})
    llm = FakeLlm([LlmReply("", [call("get_card_details", {"card_alias": "hdfc-regalia"})]),
                   LlmReply("I couldn't find that card.")])
    r = make(llm, mcp).run_turn([], "Tell me about regalia")
    tool_msg = [m for m in llm.seen[1]["messages"] if m["role"] == "tool"][0]
    assert '"tool_error"' in tool_msg["content"] and "Card not found" in tool_msg["content"]
    assert r.error is None and r.trace[0].result.error_kind == "tool_error"


def test_malformed_arguments_do_not_reach_server(live_catalog):
    mcp = FakeMcp(live_catalog)
    llm = FakeLlm([LlmReply("", [call("recommend_cards", "{not json")]), LlmReply("Sorry.")])
    r = make(llm, mcp).run_turn([], "hi")
    assert mcp.calls == [] and r.trace[0].result.error_kind == "bad_arguments"


def test_unknown_tool_blocked(live_catalog):
    mcp = FakeMcp(live_catalog)
    llm = FakeLlm([LlmReply("", [call("run_api_diagnostics", {})]), LlmReply("ok")])
    r = make(llm, mcp).run_turn([], "hi")
    assert mcp.calls == [] and r.trace[0].result.error_kind == "unknown_tool"


def test_max_rounds_stops_loop(live_catalog):
    mcp = FakeMcp(live_catalog)
    loop = [LlmReply("", [call("list_cards", {}, cid=f"c{i}")]) for i in range(2)]
    llm = FakeLlm(loop + [LlmReply("Here is what I have.")])
    r = make(llm, mcp, max_rounds=2).run_turn([], "hi")
    assert r.hit_max_rounds and len(mcp.calls) == 2
    assert llm.seen[-1]["tools"] is None
    assert llm.seen[-1]["messages"][-1]["content"] == prompts.MAX_ROUNDS_NOTE


def test_mcp_unavailable_on_connect():
    class Down:
        async def __aenter__(self):
            raise ConnectionError("refused")

        async def __aexit__(self, *a):
            return None

    r = Agent(settings(), FakeLlm([]), session_factory=Down).run_turn([], "hi")
    assert r.error == "mcp_unavailable" and r.answer == prompts.SERVICE_UNAVAILABLE


def test_tool_unavailable_mid_turn_is_reported_to_model(live_catalog):
    down = ToolResult(ok=False, error_kind=UNAVAILABLE, error_msg="card service unavailable after retry")
    mcp = FakeMcp(live_catalog, {"recommend_cards": down})
    llm = FakeLlm([LlmReply("", [call("recommend_cards", {})]), LlmReply("Service is busy, try later.")])
    r = make(llm, mcp).run_turn([], "hi")
    assert r.error is None and r.trace[0].result.error_kind == UNAVAILABLE


def test_llm_error_is_friendly(live_catalog):
    r = make(FakeLlm([LlmError("401 bad key")]), FakeMcp(live_catalog)).run_turn([], "hi")
    assert r.error == "llm_error" and r.answer == prompts.LLM_UNAVAILABLE


def test_missing_catalog_tool(live_catalog):
    trimmed = [t for t in live_catalog if t["name"] != "check_eligibility"]
    r = make(FakeLlm([]), FakeMcp(trimmed)).run_turn([], "hi")
    assert r.error == "catalog" and "check_eligibility" in r.error_detail


BAD = "Get HDFC Millenia; you'll net ₹7,820 in year one and you will definitely get approved."


def test_guardrails_off_reports_only(live_catalog, amazon_result):
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    llm = FakeLlm([LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]), LlmReply(BAD)])
    r = make(llm, mcp).run_turn([], "15k on Amazon")
    assert r.answer == BAD and not r.regenerated
    assert r.validation.rules() == ["approval_promise", "unreturned_rupee"]
    assert prompts.GUARDED_ADDENDUM not in llm.seen[0]["messages"][0]["content"]


def test_guardrails_on_regenerates(live_catalog, amazon_result):
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    good = "HDFC Millenia returns ₹9,000 a year; approval is the bank's decision."
    llm = FakeLlm([LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]), LlmReply(BAD), LlmReply(good)])
    r = make(llm, mcp, guardrails="on").run_turn([], "15k on Amazon")
    assert r.regenerated and not r.fell_back and r.answer == good and r.validation.ok
    assert r.first_answer == BAD and not r.first_validation.ok
    assert "₹7,820" in llm.seen[-1]["messages"][-1]["content"]          # feedback lists the violation
    assert prompts.GUARDED_ADDENDUM in llm.seen[0]["messages"][0]["content"]
    assert r.history[-1] == {"role": "assistant", "content": good}
    assert not any("[automatic check]" in str(m.get("content")) for m in r.history)


def test_guardrails_on_falls_back(live_catalog, amazon_result):
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    llm = FakeLlm([LlmReply("", [call("recommend_cards", {})]), LlmReply(BAD), LlmReply(BAD)])
    r = make(llm, mcp, guardrails="on").run_turn([], "15k on Amazon")
    assert r.fell_back and r.answer == prompts.FALLBACK_ANSWER and r.validation.ok


def test_followup_can_cite_earlier_tool_result(live_catalog, amazon_result):
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    agent = make(FakeLlm([LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]),
                          LlmReply("Top pick: HDFC Millenia."),
                          LlmReply("Its joining fee is ₹1,180.")]), mcp)
    t1 = agent.run_turn([], "15k on Amazon")
    t2 = agent.run_turn(t1.history, "what's the joining fee?")
    assert t2.validation.ok and t2.trace == []


def test_usage_summed_across_calls(live_catalog):
    mcp = FakeMcp(live_catalog)
    llm = FakeLlm([LlmReply("", [call("list_cards", {})], usage={"prompt_tokens": 100, "completion_tokens": 5, "cost": 0.001}),
                   LlmReply("done", usage={"prompt_tokens": 200, "completion_tokens": 10, "cost": 0.002})])
    r = make(llm, mcp).run_turn([], "hi")
    assert r.usage == {"llm_calls": 2, "prompt_tokens": 300, "completion_tokens": 15, "cost": pytest.approx(0.003)}


def test_catalog_cached_until_ttl_then_refetched(live_catalog, monkeypatch):
    from dataclasses import replace

    class Counting(FakeMcp):
        lists = 0

        async def list_tools(self):
            Counting.lists += 1
            return self.catalog

    mcp = Counting(live_catalog)
    agent = Agent(replace(settings(), catalog_ttl_s=100), FakeLlm([LlmReply("a"), LlmReply("b"), LlmReply("c")]),
                  session_factory=lambda: mcp)
    clock = [0.0]
    monkeypatch.setattr("app.agent.orchestrator.time.monotonic", lambda: clock[0])
    agent.run_turn([], "1")
    agent.run_turn([], "2")
    assert Counting.lists == 1
    clock[0] = 101
    agent.run_turn([], "3")
    assert Counting.lists == 2
    assert set(agent.tool_schemas()) <= {"get_advisor_context", "recommend_cards", "get_card_details", "list_cards",
                                         "compare_cards", "check_eligibility", "whatsapp_resolve_card_or_category"}


def test_bug_in_our_code_is_internal_error_not_mcp_outage(live_catalog, monkeypatch):
    def broken(*a, **k):
        raise KeyError("validator bug")

    monkeypatch.setattr("app.agent.orchestrator.validate", broken)
    r = make(FakeLlm([LlmReply("answer")]), FakeMcp(live_catalog)).run_turn([], "hi")
    assert r.error == "internal_error" and "validator bug" in r.error_detail
    assert r.answer == prompts.INTERNAL_ERROR


def test_connect_failure_is_still_mcp_unavailable(live_catalog):
    class Down(FakeMcp):
        async def __aenter__(self):
            raise ConnectionError("refused")

    r = make(FakeLlm([]), Down(live_catalog)).run_turn([], "hi")
    assert r.error == "mcp_unavailable" and "connect" in r.error_detail


def test_session_is_closed_even_when_the_loop_fails(live_catalog):
    class Tracking(FakeMcp):
        closed = False

        async def __aexit__(self, *a):
            Tracking.closed = True

    mcp = Tracking(live_catalog)
    make(FakeLlm([LlmError("down")]), mcp).run_turn([], "hi")
    assert Tracking.closed


def test_guardrails_prompt_adds_rupee_rule_without_rewrite(live_catalog, amazon_result):
    """GUARDRAILS=prompt (Task 4, E04): the ₹ rule is in the system prompt, the validator still
    only reports, and nothing is regenerated, so before/after isolates the prompt change."""
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    llm = FakeLlm([LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]), LlmReply(BAD)])
    r = make(llm, mcp, guardrails="prompt").run_turn([], "15k on Amazon")
    system = llm.seen[0]["messages"][0]["content"]
    assert prompts.RUPEE_RULE in system
    assert "tax advice" not in system and "promise or imply approval" not in system   # other rules not bundled
    assert r.answer == BAD and not r.regenerated and len(llm.seen) == 2
    assert "unreturned_rupee" in r.validation.rules()


def test_system_prompt_modes():
    assert prompts.system_prompt("off") == prompts.BASELINE
    assert prompts.system_prompt("prompt") == prompts.BASELINE + prompts.PROMPT_ADDENDUM
    assert prompts.RUPEE_RULE in prompts.system_prompt("on") and "tax advice" in prompts.system_prompt("on")
    assert "[Z] months" in prompts.RUPEE_RULE          # explicitly overrides the server playbook line
    assert "point value" in prompts.RUPEE_RULE         # Q07 residual: points x value is a calculation too
    for mode in ("prompt", "on"):                       # E07: monthly-field fact in both rule modes
        assert prompts.MONTHLY_FIELD_NOTE in prompts.system_prompt(mode)
    assert "annual_value" not in prompts.system_prompt("off")
    for mode in ("prompt", "on"):                       # fee/waiver rule tied to returned fields
        assert prompts.FEE_RULE in prompts.system_prompt(mode)
    assert "annual_fee_waived" not in prompts.system_prompt("off")
    # no eval-case content in the rules (anti-overfitting): card names or figures from evals/questions.json outputs
    for token in ("Millenia", "Millennia", "Cashback", "Magnus", "Times Black", "Ornge", "Landmark",
                  "₹750", "₹9,000", "₹15,000", "₹30,000", "12,000 points", "₹0.25"):
        assert token not in prompts.PROMPT_ADDENDUM, token


def test_config_accepts_guardrail_modes(monkeypatch):
    import pytest
    from app.config import ConfigError, load_settings

    for mode in ("off", "prompt", "on"):
        monkeypatch.setenv("GUARDRAILS", mode)
        assert load_settings(require_key=False).guardrails == mode
    monkeypatch.setenv("GUARDRAILS", "enforce")
    with pytest.raises(ConfigError):
        load_settings(require_key=False)


def run_with_events(guardrails, live_catalog, amazon_result, *replies):
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    llm = FakeLlm(list(replies))
    events = []
    r = make(llm, mcp, guardrails=guardrails).run_turn([], "I spend 15k a month on Amazon", on_event=events.append)
    return r, events, llm


def test_streaming_events_build_the_answer(live_catalog, amazon_result):
    answer = "HDFC Millenia: ₹9,000 a year, joining fee ₹1,180."
    r, events, llm = run_with_events(
        "prompt", live_catalog, amazon_result,
        LlmReply("Let me check.", [call("recommend_cards", {"amazon_spends": 15000})]),
        LlmReply(answer))
    kinds = [e[0] for e in events]
    assert kinds[:2] == ["text", "text"] and "discard" in kinds  # preamble streamed, then dropped
    after = events[kinds.index("discard") + 1:]
    assert after[0] == ("tool_call", "recommend_cards")
    assert "".join(e[1] for e in after if e[0] == "text") == answer == r.answer
    assert all(seen["streamed"] for seen in llm.seen)


def test_enforced_mode_never_streams_text(live_catalog, amazon_result):
    r, events, llm = run_with_events(
        "on", live_catalog, amazon_result,
        LlmReply("", [call("recommend_cards", {"amazon_spends": 15000})]),
        LlmReply("You'd save ₹12,345 a year."),         # fails the ₹ check -> rewritten
        LlmReply("HDFC Millenia: ₹9,000 a year."))
    assert r.regenerated and r.answer == "HDFC Millenia: ₹9,000 a year."
    assert events == [("tool_call", "recommend_cards")]  # progress only; no unchecked text shown
    assert not any(seen["streamed"] for seen in llm.seen)


def test_no_callback_means_no_streaming(live_catalog, amazon_result):
    mcp = FakeMcp(live_catalog, {"recommend_cards": amazon_result})
    llm = FakeLlm([LlmReply("Tell me your spends.")])
    make(llm, mcp, guardrails="prompt").run_turn([], "hi")  # the eval runner's path
    assert llm.seen[0]["streamed"] is False


class _Stream:
    def __init__(self, chunks):
        self.chunks = chunks

    def __enter__(self):
        return iter(self.chunks)

    def __exit__(self, *a):
        return None


def _chunk(content=None, tool_calls=None, finish=None, usage=None, error=None):
    from types import SimpleNamespace as NS
    choices = [] if usage else [NS(delta=NS(content=content, tool_calls=tool_calls), finish_reason=finish)]
    return NS(error=error, model="fake/model", usage=usage, choices=choices)


def _openrouter_llm(chunks, sent):
    from types import SimpleNamespace as NS
    from app.agent.llm import OpenRouterLlm
    llm = OpenRouterLlm.__new__(OpenRouterLlm)
    llm.settings = settings()

    def send(**kw):
        sent.update(kw)
        return _Stream(chunks)

    llm._client = NS(chat=NS(send=send))
    return llm


def test_stream_assembles_text_tool_calls_and_usage():
    from types import SimpleNamespace as NS
    usage = NS(model_dump=lambda exclude_none: {"prompt_tokens": 10, "cost": 0.001})
    tc = lambda i, **kw: NS(index=i, id=kw.get("id"), function=NS(name=kw.get("name"), arguments=kw.get("args")))
    chunks = [_chunk("Let me "), _chunk("check."),
              _chunk(tool_calls=[tc(0, id="c1", name="recommend_cards", args='{"amazon_')]),
              _chunk(tool_calls=[tc(0, args='spends": 15000}')]),
              _chunk(tool_calls=[tc(1, id="c2", name="list_cards")], finish="tool_calls"),
              _chunk(usage=usage)]
    sent, deltas = {}, []
    reply = _openrouter_llm(chunks, sent).chat([{"role": "user", "content": "hi"}], [{"type": "function"}],
                                               on_text=deltas.append)
    assert sent["stream"] is True and sent["stream_options"] == {"include_usage": True}
    assert deltas == ["Let me ", "check."] and reply.text == "Let me check."
    assert reply.tool_calls == [
        {"id": "c1", "type": "function", "function": {"name": "recommend_cards", "arguments": '{"amazon_spends": 15000}'}},
        {"id": "c2", "type": "function", "function": {"name": "list_cards", "arguments": "{}"}}]
    assert reply.finish_reason == "tool_calls" and reply.usage == {"prompt_tokens": 10, "cost": 0.001}


def test_stream_error_chunk_raises_llm_error():
    from types import SimpleNamespace as NS
    llm = _openrouter_llm([_chunk("Hi"), _chunk(error=NS(code=502, message="upstream died"))], {})
    with pytest.raises(LlmError, match="upstream died"):
        llm.chat([{"role": "user", "content": "hi"}], on_text=lambda d: None)
