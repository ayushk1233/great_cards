"""Per-turn checks, case status, run store, resume and the runner loop (offline, fake agent)."""

import json
from pathlib import Path

import pytest

from app.agent.orchestrator import TraceEntry, TurnResult
from app.agent.validation import ValidationReport, Violation
from app.evaluation import runner
from app.evaluation.cases import CaseFileError, load_cases
from app.evaluation.checks import (ERROR_INTERNAL, FAIL_AUTO, HARD, INCONCLUSIVE_INFRA, INFO, INFRA, NEEDS_REVIEW, case_status,
                                   check_turn)
from app.evaluation.store import ResumeMismatchError, RunLockedError, RunStore
from app.mcp.client import ToolResult

SCHEMAS = {"recommend_cards": {"properties": {"amazon_spends": {}, "online_food_ordering": {}}},
           "check_eligibility": {"properties": {"pincode": {}, "annual_income": {}, "employment_status": {}}}}


def turn(answer, calls=(), violations=(), error=None):
    trace = []
    for c in calls:
        tool, args, res = (c + (ToolResult(ok=True, data={}, raw_text="{}"),))[:3] if isinstance(c, tuple) else (c, {}, ToolResult(ok=True, data={}))
        trace.append(TraceEntry(1, tool, args, res))
    return TurnResult(answer, trace=trace, validation=ValidationReport(list(violations)), error=error,
                      history=[{"role": "assistant", "content": answer}])


def codes(flags, kind=None):
    return [f.code for f in flags if kind is None or f.kind == kind]


# ---------------------------------------------------------------- check_turn
def test_arg_match_is_numeric_and_type_tolerant():
    r = turn("ok", [("check_eligibility", {"annual_income": "600000", "pincode": "110001"})])
    exp = {"must_call": [{"tool": "check_eligibility", "args": {"annual_income": 600000, "pincode": "110001"}}]}
    assert codes(check_turn(exp, r, SCHEMAS), HARD) == []
    bad = turn("ok", [("check_eligibility", {"annual_income": "50k", "pincode": "110001"})])
    assert codes(check_turn(exp, bad, SCHEMAS), HARD) == ["arg_mismatch"]


def test_missing_and_unexpected_tool_calls():
    exp = {"must_call": [{"tool": "recommend_cards"}], "must_not_call": ["check_eligibility"]}
    flags = check_turn(exp, turn("ok", [("check_eligibility", {})]), SCHEMAS)
    assert codes(flags, HARD) == ["missing_tool_call", "unexpected_tool_call"]


def test_G1_unknown_argument_key():
    r = turn("ok", [("recommend_cards", {"amazon_spends": 1, "ott_spends": 1500})])
    assert [str(f) for f in check_turn({}, r, SCHEMAS) if f.kind == HARD] == ["unknown_arg_key:recommend_cards.ott_spends"]


def test_G2_G5_G6_generic_checks():
    refused = ("recommend_cards", {}, ToolResult(ok=False, error_kind="call_budget"))
    r = turn("", [("recommend_cards", {})] * 6 + [refused], violations=[Violation("unreturned_rupee", "d", "₹7,820")])
    flags = check_turn({}, r, SCHEMAS)
    assert codes(flags, HARD) == ["guardrail_unreturned_rupee", "tool_call_budget_exceeded", "empty_answer"]
    assert codes(flags, INFO) == []                     # a refused call is not reported as a tool error


def test_internal_error_is_its_own_status():
    flags = check_turn({}, turn("oops", error="internal_error"), SCHEMAS)
    assert [(f.kind, f.code) for f in flags] == [("internal", "internal_error")]
    assert case_status([[f.as_dict() for f in flags]], False) == ERROR_INTERNAL
    assert codes(check_turn({}, turn("slow", error="turn_timeout"), SCHEMAS), INFRA) == ["turn_error"]


def test_tool_error_is_info_but_bad_arguments_is_hard():
    r = turn("Not found.", [("get_card_details", {}, ToolResult(ok=False, error_kind="tool_error", error_msg="Card not found")),
                            ("get_card_details", "{bad", ToolResult(ok=False, error_kind="bad_arguments"))])
    flags = check_turn({}, r, SCHEMAS)
    assert codes(flags, INFO) == ["tool_tool_error"] and codes(flags, HARD) == ["bad_arguments"]


def test_infra_errors():
    assert codes(check_turn({}, turn("busy", error="mcp_unavailable"), SCHEMAS)) == ["turn_error"]
    r = turn("x", [("recommend_cards", {}, ToolResult(ok=False, error_kind="unavailable"))])
    assert codes(check_turn({}, r, SCHEMAS), INFRA) == ["tool_unavailable"]


def test_refusal_phrases_and_results():
    exp = {"must_refuse": True, "forbidden_phrases": ["ABCDE1234F"]}
    assert codes(check_turn(exp, turn("I can't guarantee approval; please don't share your PAN."))) == []
    assert codes(check_turn(exp, turn("Sure ABCDE1234F, you're approved!"))) == ["refusal_missing", "forbidden_phrase"]
    exp = {"required_any": [["2,950"], ["4 lakh", "4,00,000"]], "tool_result_contains": ["SBI Cashback"]}
    r = turn("Fee ₹2,950, waived at ₹4,00,000.", [("get_card_details", {}, ToolResult(ok=True, data={}, raw_text='{"card_name":"SBI CASHBACK"}'))])
    assert codes(check_turn(exp, r)) == []
    assert codes(check_turn(exp, turn("Fee ₹2,950."))) == ["required_missing", "tool_result_missing"]


def test_zero_or_absent_and_must_call_any_and_must_succeed():
    exp = {"zero_or_absent": {"recommend_cards": ["online_food_ordering"]}, "must_call_any": ["list_cards", "recommend_cards"],
           "must_succeed": ["recommend_cards"]}
    ok = turn("x", [("recommend_cards", {"online_food_ordering": 0})])
    assert codes(check_turn(exp, ok, SCHEMAS)) == []
    bad = turn("x", [("recommend_cards", {"online_food_ordering": 10000}, ToolResult(ok=False, error_kind="tool_error"))])
    assert codes(check_turn(exp, bad, SCHEMAS), HARD) == ["no_successful_call", "nonzero_arg"]


def test_case_status_never_passes():
    f = lambda kind: [{"kind": kind, "code": "x", "detail": ""}]
    assert case_status([[], []], True) == NEEDS_REVIEW
    assert case_status([f(INFO)], True) == NEEDS_REVIEW
    assert case_status([f(HARD)], True) == FAIL_AUTO
    assert case_status([f(HARD), f(INFRA)], True) == INCONCLUSIVE_INFRA
    assert case_status([[]], False) == INCONCLUSIVE_INFRA


# ---------------------------------------------------------------- case file
def test_questions_file_is_valid():
    cases, cross = load_cases(Path("evals/questions.json"))
    assert len(cases) == 20 and sum(len(q["turns"]) for q in cases) == 29
    assert {x["id"] for x in cross} == {"X1", "X2", "X3"}


def test_case_file_validation(tmp_path):
    p = tmp_path / "q.json"
    p.write_text(json.dumps({"questions": [{"id": "A", "turns": [{"user": "hi", "expect": {"must_cal": []}}]},
                                           {"id": "A", "turns": ["x"]}]}))
    with pytest.raises(CaseFileError, match="unknown expectation keys.*duplicate|duplicate.*unknown|unknown"):
        load_cases(p)


# ---------------------------------------------------------------- store
def test_store_append_load_torn_line_and_pending(tmp_path):
    cases = [{"id": "A", "sha": "1"}, {"id": "B", "sha": "2"}, {"id": "C", "sha": "3"}]
    with RunStore(tmp_path) as s:
        s.append({"id": "A", "case_sha": "1", "status": NEEDS_REVIEW})
        s.append({"id": "B", "case_sha": "2", "status": INCONCLUSIVE_INFRA})
        with s.results_path.open("a") as fh:
            fh.write('{"id": "C", "case_sha": "3", "sta')        # crash mid-write
        s.append({"id": "C", "case_sha": "OLD", "status": FAIL_AUTO})
        assert set(s.load()) == {"A", "B", "C"}
        assert [q["id"] for q in s.pending(cases)] == ["B", "C"]               # infra retried, C changed
        assert [q["id"] for q in s.pending(cases, retry_infra=False)] == ["C"]


def test_store_lock_is_exclusive(tmp_path):
    with RunStore(tmp_path):
        with pytest.raises(RunLockedError):
            RunStore(tmp_path).__enter__()


def test_resume_refuses_incomparable_settings(tmp_path):
    h = {"mode": "off", "model": "m", "temperature": 0, "prompt_sha": "p", "questions_file": "q",
         "server": {"catalog_sha256_12": "a"}, "git": "g1"}
    s = RunStore(tmp_path)
    s.write_header(h)
    assert s.check_resumable({**h, "server": {"catalog_sha256_12": "b"}, "git": "g2"})  # warnings only
    with pytest.raises(ResumeMismatchError, match="mode"):
        s.check_resumable({**h, "mode": "on"})


# ---------------------------------------------------------------- runner end to end (fake agent, no network)
class FakeAgent:
    """Scripted per user message: an answer, a crash, or an infra error."""

    def __init__(self, script):
        from tests.test_orchestrator import settings
        self.script, self.seen, self.settings = script, [], settings()

    def prime_catalog(self, tools):
        pass

    def tool_schemas(self):
        return SCHEMAS

    def run_turn(self, history, msg):
        self.seen.append(msg)
        act = self.script.get(msg, "ok")
        if act == "crash":
            raise RuntimeError("process died")
        if act == "infra":
            return turn("busy", error="mcp_unavailable")
        if act == "bug":
            return turn("oops", error="internal_error")
        return turn(f"re: {msg}", [("recommend_cards", {"amazon_spends": 1})])


class FakeLimiter:
    def wait_for_capacity(self, slots):
        return 0.0

    def snapshot(self):
        return {"requests": 0, "waited_s": 0.0, "throttled_429": 0, "max_requests": 50, "window_s": 180.0}


@pytest.fixture
def harness(tmp_path, monkeypatch):
    qfile = tmp_path / "q.json"
    qfile.write_text(json.dumps({"questions": [
        {"id": "A", "category": "c", "turns": [{"user": "a1", "expect": {"must_call": [{"tool": "recommend_cards"}]}}, "a2"]},
        {"id": "B", "category": "c", "turns": ["b1"]},
        {"id": "C", "category": "c", "turns": ["c1"]},
        {"id": "D", "category": "c", "turns": ["d1"]}],
        "cross_checks": [{"id": "X", "type": "review", "detail": "d"}]}))
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(runner, "build_limiter", lambda s: FakeLimiter())

    async def fake_catalog(settings, limiter):
        return {"name": "fake", "version": "0", "catalog_sha256_12": "abc"}, []

    monkeypatch.setattr(runner, "_fetch_catalog", fake_catalog)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setenv("MCP_RATE_STATE", "")
    state = {"agents": []}

    def use(script):
        def factory(settings, limiter=None):
            a = FakeAgent(script)
            state["agents"].append(a)
            return a
        monkeypatch.setattr(runner, "build_agent", factory)
    return qfile, use, state


def _run_dir(tmp_path):
    return next((tmp_path / "reports").iterdir())


def test_crash_then_resume_runs_only_the_rest(harness, tmp_path):
    qfile, use, state = harness
    use({"c1": "crash"})
    with pytest.raises(RuntimeError):
        runner.main(["--file", str(qfile)])
    run_dir = _run_dir(tmp_path)
    assert set(RunStore(run_dir).load()) == {"A", "B"}             # finished cases survived the crash

    use({})
    assert runner.main(["--file", str(qfile), "--resume", "latest"]) == 0
    assert state["agents"][-1].seen == ["c1", "d1"]                  # A and B were not re-run
    recs = RunStore(run_dir).load()
    assert set(recs) == {"A", "B", "C", "D"} and recs["A"]["status"] == NEEDS_REVIEW
    assert len(recs["A"]["turns"]) == 2                              # multi-turn case kept whole
    for f in ("summary.md", "transcripts.md", "tools.md", "review.md"):
        assert (run_dir / f).exists()
    assert len(json.loads((run_dir / "run.json").read_text())["resumes"]) == 1


def test_circuit_breaker_stops_and_infra_is_retried_on_resume(harness, tmp_path):
    qfile, use, state = harness
    use({"b1": "infra", "c1": "infra"})
    assert runner.main(["--file", str(qfile)]) == 2                   # stopped early
    assert state["agents"][-1].seen == ["a1", "a2", "b1", "c1"]       # D never attempted
    run_dir = _run_dir(tmp_path)
    assert not (run_dir / "review.md").exists()                       # only written once complete
    use({})
    assert runner.main(["--file", str(qfile), "--resume", str(run_dir)]) == 0
    assert state["agents"][-1].seen == ["b1", "c1", "d1"]
    assert RunStore(run_dir).load()["B"]["attempt"] == 2


def test_dry_run_and_report_need_no_network_or_key(harness, tmp_path, monkeypatch, capsys):
    qfile, use, state = harness
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setattr(runner, "_fetch_catalog", None)                # would crash if called
    assert runner.main(["--file", str(qfile), "--dry-run"]) == 0
    assert "4/4 cases, 5 turns" in capsys.readouterr().out


def test_resume_with_other_mode_is_refused(harness, tmp_path):
    qfile, use, state = harness
    use({})
    assert runner.main(["--file", str(qfile), "--only", "B"]) == 0
    run_dir = _run_dir(tmp_path)
    assert runner.main(["--file", str(qfile), "--mode", "on", "--resume", str(run_dir)]) == 1


def test_parallel_workers_record_every_case(harness, tmp_path):
    qfile, use, state = harness
    use({})
    assert runner.main(["--file", str(qfile), "--workers", "3"]) == 0
    assert set(RunStore(_run_dir(tmp_path)).load()) == {"A", "B", "C", "D"}


def test_internal_errors_trip_the_breaker_and_are_retried(harness, tmp_path):
    qfile, use, state = harness
    use({"a1": "bug", "b1": "bug"})
    assert runner.main(["--file", str(qfile)]) == 2
    run_dir = _run_dir(tmp_path)
    assert RunStore(run_dir).load()["A"]["status"] == ERROR_INTERNAL
    use({})
    assert runner.main(["--file", str(qfile), "--resume", "latest"]) == 0
    assert state["agents"][-1].seen == ["a1", "a2", "b1", "c1", "d1"]
