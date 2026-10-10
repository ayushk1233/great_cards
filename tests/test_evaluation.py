"""checks.py flags and runner.run_question with a fake agent (offline)."""

from app.agent.orchestrator import TraceEntry, TurnResult
from app.agent.validation import ValidationReport, Violation
from app.evaluation.checks import run_checks
from app.evaluation.runner import run_question
from app.mcp.client import ToolResult


def turn(answer, tools=(), violations=(), error=None):
    trace = [TraceEntry(1, t, {}, ToolResult(ok=True, data={})) for t in tools]
    return TurnResult(answer, trace=trace, validation=ValidationReport(list(violations)), error=error,
                      history=[{"role": "assistant", "content": answer}])


def test_flags_missing_tool_and_violation():
    q = {"expectations": {"must_call_tools": ["recommend_cards"]}}
    r = turn("Get X.", violations=[Violation("unreturned_rupee", "d", "₹7,820")])
    assert run_checks(q, r) == ["guardrail:unreturned_rupee:₹7,820", "missing_tool_call:recommend_cards"]


def test_refusal_detection():
    q = {"expectations": {"must_refuse": True}}
    assert run_checks(q, turn("I can't give tax advice; please consult a CA.")) == []
    assert run_checks(q, turn("You will save ₹50,000 in tax.")) == ["expected_refusal_missing"]


def test_clean_answer_has_no_flags():
    q = {"expectations": {"must_call_tools": ["get_card_details"], "required_phrases": ["annual fee"]}}
    assert run_checks(q, turn("The annual fee is listed above.", tools=["get_card_details"])) == []


def test_run_question_multi_turn():
    class FakeAgent:
        def __init__(self):
            self.histories = []

        def run_turn(self, history, msg):
            self.histories.append(list(history))
            return turn(f"re: {msg}", tools=["recommend_cards"])

    agent = FakeAgent()
    q = {"id": "Q1", "category": "mixed", "turns": ["a", "b"], "expectations": {"must_call_tools": ["recommend_cards"]}}
    res = run_question(agent, q)
    assert [t["answer"] for t in res["turns"]] == ["re: a", "re: b"]
    assert agent.histories[1] == [{"role": "assistant", "content": "re: a"}]  # history threaded
    assert res["flags"] == []


def test_refusal_live_phrasing():
    q = {"expectations": {"must_refuse": True}}
    assert run_checks(q, turn("I can't confirm approval or estimate tax savings yet.")) == []
    assert run_checks(q, turn("Approval isn't guaranteed even if you meet the criteria.")) == []
