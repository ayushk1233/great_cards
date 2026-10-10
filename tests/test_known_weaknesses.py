"""Known weaknesses in OUR implementation: the smallest test that exposes each one.

Every test asserts the behaviour we WANT and is marked xfail(strict=True), so today it
"xfails" (weakness confirmed). If a fix lands, or the claim was wrong, it XPASSes and the
suite fails, forcing this file to be updated. Nothing here changes runtime behaviour.
Fixes require explicit approval (see PROGRESS.md).
"""

import json

import pytest

from app.agent.validation import check_approval_promise, check_tax_advice, check_unreturned_rupees, allowed_amounts, validate
from app.mcp.client import RETRY_BACKOFF_S, ToolResult, normalize
from tests.test_orchestrator import FakeLlm, FakeMcp, call, make, settings
from app.agent.llm import LlmReply

weak = pytest.mark.xfail(strict=True, reason="known weakness: see docstring")
USER = ["I spend ₹15,000 a month on Amazon. Which card?"]


@pytest.fixture
def amazon(raw):
    return raw("recommend__amazon_15k")["parsed_content"][0]


@pytest.fixture
def playbook(raw):
    return raw("context__advisor_full")["parsed_content"][0]


# ---------------------------------------------------------------- numerical grounding (₹ guardrail)

@weak
def test_W1_misattributed_figure_is_flagged(amazon):
    """W1 (S2). The ₹ guardrail checks that a number is PRESENT somewhere in tool output, not that
    it belongs to the card it is attached to. ₹8,411 is BOB/CRED's net; Millenia's is ₹9,000."""
    assert not validate("HDFC Millenia nets you ₹8,411 a year.", [amazon], USER).ok


@weak
def test_W2_playbook_examples_do_not_whitelist_figures(playbook):
    """W2 (S2). get_advisor_context is guidance, but its 17 example ₹ values (₹5,000, ₹10,000,
    ₹11,800, ...) enter the allowed set, so an invented '₹10,000 lounge value' passes."""
    assert not validate("Its lounge access is worth ₹10,000 a year.", [playbook], ["Best card for lounges?"]).ok


@weak
def test_W3_unmarked_amounts_are_checked(amazon):
    """W3 (S2). Only currency-marked amounts are extracted; '7,820 in year one' (no ₹) slips through."""
    assert check_unreturned_rupees("You'd net 7,820 in your first year.", allowed_amounts([amazon], USER))


@weak
def test_W4_invented_reward_rate_is_flagged(amazon):
    """W4 (S2). Only ₹ is guarded; an invented percentage (10% on Amazon) is never checked."""
    assert not validate("SBI Cashback gives you 10% back on Amazon.", [amazon], USER).ok


@weak
def test_W5_stale_turn1_figure_is_flagged(amazon, raw):
    """W5 (S2). Figures from ANY earlier turn stay allowed. After the user changes spends, quoting
    a figure from the old profile (₹8,411 from the ₹15k run) still passes."""
    new_profile = raw("followup__amazon_50k_top25")["parsed_content"][0]
    rep = validate("At ₹50,000 a month, BOB Cashback nets ₹8,411.", [amazon, new_profile],
                   USER + ["Actually I spend ₹50,000 a month on Amazon."])
    assert not rep.ok


@weak
def test_W6_rupee_range_is_not_a_false_positive(amazon):
    """W6 (S4, noise). '₹8–9k' parses '₹8' as eight rupees -> spurious violation (false positive)."""
    assert check_unreturned_rupees("about ₹8–9k a year", allowed_amounts([amazon], USER)) == []


# ---------------------------------------------------------------- approval / tax detectors

@weak
def test_W7_eligibility_claim_is_flagged():
    """W7 (S1). 'You're eligible' for a card the user cannot get (C3 Regalia at ₹6L) is the worst
    eligibility failure, but the approval detector only matches approval/guarantee wording."""
    assert check_approval_promise("Yes, you're eligible for the HDFC Regalia Gold.")


@weak
def test_W8_disclaimer_does_not_launder_tax_advice():
    """W8 (S1). Any sentence containing 'consult' is skipped, so advice + disclaimer passes."""
    assert check_tax_advice("You can claim the annual fee under Section 80C, but consult a CA.")


@weak
def test_W9_bare_deductible_is_flagged():
    """W9 (S1). 'deductible' without 'under ...' is not matched."""
    assert check_tax_advice("The annual fee is deductible as a business expense.")


# ---------------------------------------------------------------- orchestrator

@weak
def test_W10_empty_final_answer_gets_fallback(live_catalog):
    """W10 (S3). If the model returns empty text after tools, the user gets an empty bubble."""
    llm = FakeLlm([LlmReply("", [call("list_cards", {})]), LlmReply("")])
    r = make(llm, FakeMcp(live_catalog)).run_turn([], "hi")
    assert r.answer.strip() != ""


@weak
def test_W11_per_turn_tool_call_budget(live_catalog):
    """W11 (S2, prod server). Rounds are capped (6) but calls per round are not: one reply with
    12 tool calls sends 12 MCP requests in a single turn (rate limit ~65 per 3 min)."""
    burst = [call("get_card_details", {"card_alias": f"x{i}"}, cid=f"c{i}") for i in range(12)]
    mcp = FakeMcp(live_catalog)
    make(FakeLlm([LlmReply("", burst), LlmReply("done")]), mcp).run_turn([], "hi")
    assert len(mcp.calls) <= 8


@weak
def test_W12_unknown_argument_keys_rejected_client_side(live_catalog):
    """W12 (S2). The server silently drops unknown keys (C9). We forward them unvalidated, so a
    spend the model mapped to an invented key ('ott_spends') vanishes without anyone noticing."""
    mcp = FakeMcp(live_catalog)
    make(FakeLlm([LlmReply("", [call("recommend_cards", {"ott_spends": 1500})]), LlmReply("ok")]), mcp).run_turn([], "hi")
    assert mcp.calls == []


@weak
def test_W13_playbook_not_duplicated_in_history(live_catalog, raw):
    """W13 (S3, cost). Every get_advisor_context result (~42k chars) stays in history forever; 3
    calls = 3 copies. Long chats cross 100k prompt tokens, where Haiku pricing goes up 5x."""
    pb = normalize(raw("context__advisor_full")["raw_result"])
    mcp = FakeMcp(live_catalog, {"get_advisor_context": pb})
    replies = []
    for i in range(3):
        replies += [LlmReply("", [call("get_advisor_context", {"topic": "full"}, cid=f"c{i}")]), LlmReply(f"a{i}")]
    agent, history = make(FakeLlm(replies), mcp), []
    for i in range(3):
        history = agent.run_turn(history, f"q{i}").history
    copies = sum(1 for m in history if m["role"] == "tool" and "SECTION 1" in m["content"])
    assert copies <= 1


@weak
def test_W14_tool_catalog_cached_across_turns(live_catalog):
    """W14 (S3, prod server). The approved plan says tools/list is cached per process; the code
    lists tools on every turn (one extra MCP request per turn)."""
    class Counting(FakeMcp):
        lists = 0

        async def list_tools(self):
            Counting.lists += 1
            return self.catalog

    mcp = Counting(live_catalog)
    agent = make(FakeLlm([LlmReply("a"), LlmReply("b"), LlmReply("c")]), mcp)
    h = []
    for q in ("1", "2", "3"):
        h = agent.run_turn(h, q).history
    assert Counting.lists == 1


@weak
def test_W15_turn_has_a_bounded_worst_case_latency():
    """W15 (S3). No overall turn deadline: 6 rounds x (2 attempts x 20 s timeout + 3 s backoff)
    = 258 s of tool time alone, before 7 LLM calls of up to 60 s each."""
    s = settings()
    worst_tool_s = s.max_tool_rounds * (2 * s.tool_timeout_s + RETRY_BACKOFF_S)
    assert worst_tool_s <= 60
