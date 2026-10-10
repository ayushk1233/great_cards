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

    def chat(self, messages, tools=None):
        self.seen.append({"messages": messages, "tools": tools})
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
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
