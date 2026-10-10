"""Resumable, rate-limited evaluation run against the production MCP server.

    python -m app.evaluation.runner --dry-run                      # plan only: no network, no cost
    python -m app.evaluation.runner --mode off                     # new run of evals/questions.json
    python -m app.evaluation.runner --resume latest                # continue the latest run
    python -m app.evaluation.runner --resume reports/<dir> --only Q07
    python -m app.evaluation.runner --report reports/<dir>         # rebuild reports, no network

Robustness:
  - every MCP HTTP request goes through one shared RateLimiter (file-backed, cross-process);
    before each turn the runner also waits until a full turn's worth of requests fits
  - each finished case is appended + fsync'd to results.jsonl; a crash or Ctrl-C loses at most
    the case in flight, and --resume skips everything already recorded
  - resume refuses if mode / model / temperature / prompt / case file differ; re-runs a case
    whose definition changed and (by default) every INCONCLUSIVE-infra case
  - circuit breaker: stop after N consecutive infra- or internal-failed cases (don't hammer a
    struggling server, don't repeat a code bug 20 times); cost guard: stop when this
    invocation's OpenRouter spend passes --max-cost
  - per turn (orchestrator): at most MAX_TOOL_CALLS_PER_TURN MCP calls, a TURN_DEADLINE_S
    deadline, and rate-limit waits taken outside the SDK timeout (no false "unavailable")
  - an exception in our own code is ERROR-internal, never mislabelled as an MCP outage
  - --workers N runs cases in parallel threads; throughput is still capped by the limiter

Exit codes: 0 complete · 1 usage/config error · 2 stopped early (breaker/cost) · 3 MCP unreachable
· 4 run directory locked · 130 interrupted. Stopped runs print the exact resume command.
"""

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from app.agent import prompts
from app.agent.orchestrator import Agent, TurnResult, build_agent
from app.config import ROOT, ConfigError, build_limiter, load_settings
from app.evaluation.cases import CaseFileError, load_cases
from app.evaluation.checks import ERROR_INTERNAL, INCONCLUSIVE_INFRA, RETRYABLE, case_status, check_turn
from app.evaluation.report import write_reports
from app.evaluation.store import ResumeMismatchError, RunLockedError, RunStore, latest_run
from app.mcp.client import SESSION_OPEN_REQUESTS, McpSession
from app.mcp.tools import build_tool_specs

REPORTS = ROOT / "reports"
EST_REQ_PER_TURN = 6.5     # planning estimate: 4 overhead + ~2.5 tool calls
EST_COST_PER_TURN = (0.007, 0.016)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _git_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


async def _fetch_catalog(settings, limiter) -> tuple[dict, list[dict]]:
    async with McpSession(settings.mcp_url, settings.tool_timeout_s, limiter=limiter) as s:
        tools = await s.list_tools()
    specs = build_tool_specs(tools)  # raises MissingToolError if an allowlisted tool vanished
    digest = hashlib.sha256(json.dumps(specs, sort_keys=True).encode()).hexdigest()[:12]
    return {**s.server_info, "catalog_sha256_12": digest}, tools


def _trace_json(r: TurnResult) -> list[dict]:
    return [{"round": t.round, "tool": t.tool, "arguments": t.arguments, "ok": t.result.ok,
             "error_kind": t.result.error_kind, "error_msg": t.result.error_msg,
             "latency_ms": t.result.latency_ms, "raw_text": t.result.raw_text} for t in r.trace]


def turn_slots(settings) -> int:
    """HTTP requests one turn can need: session open + the call budget + the closing DELETE."""
    return SESSION_OPEN_REQUESTS + settings.max_tool_calls_per_turn + 1


def run_case(agent: Agent, q: dict, limiter=None, attempt: int = 1) -> dict:
    """All turns of one case in a fresh conversation. Stops at the first infra/internal-failed turn."""
    started, history, turns = _now(), [], []
    for t in q["turns"]:
        if limiter is not None:
            limiter.wait_for_capacity(turn_slots(agent.settings))
        r = agent.run_turn(history, t["user"])
        history = r.history
        flags = check_turn(t.get("expect"), r, agent.tool_schemas())
        turns.append({
            "user": t["user"], "answer": r.answer, "error": r.error, "error_detail": r.error_detail,
            "trace": _trace_json(r), "validation": r.validation.as_dict(), "flags": [f.as_dict() for f in flags],
            "rounds": r.rounds, "hit_max_rounds": r.hit_max_rounds, "regenerated": r.regenerated,
            "fell_back": r.fell_back, "first_answer": r.first_answer,
            "first_validation": r.first_validation.as_dict() if r.first_validation else None,
            "latency_ms": r.latency_ms, "usage": r.usage,
        })
        if r.error:
            break
    completed = len(turns) == len(q["turns"]) and not turns[-1]["error"]
    return {"id": q["id"], "category": q.get("category"), "case_sha": q["sha"], "attempt": attempt,
            "status": case_status([t["flags"] for t in turns], completed), "completed": completed,
            "started_utc": started, "finished_utc": _now(), "turns": turns}


def _cost(rec: dict) -> float:
    return sum(t.get("usage", {}).get("cost", 0) or 0 for t in rec["turns"])


def _plan(cases: list[dict], todo: list[dict], settings, run_dir: Path | None) -> str:
    turns = sum(len(q["turns"]) for q in todo)
    req = turns * EST_REQ_PER_TURN + 4
    minutes = req / settings.mcp_max_requests * settings.mcp_window_s / 60
    lo, hi = (turns * c for c in EST_COST_PER_TURN)
    return (f"plan: {len(todo)}/{len(cases)} cases, {turns} turns to run"
            + (f" (resuming {run_dir.relative_to(ROOT)})" if run_dir else "") + "\n"
            f"  ids: {' '.join(q['id'] for q in todo) or '-'}\n"
            f"  MCP: ~{req:.0f} HTTP requests, paced at {settings.mcp_max_requests}/{settings.mcp_window_s:.0f}s "
            f"-> at least ~{minutes:.0f} min\n"
            f"  LLM: {settings.llm_model}, estimated ${lo:.2f}-{hi:.2f}")


def _parse(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", choices=["off", "on"], default="off", help="guardrails report-only (off) or enforced (on)")
    ap.add_argument("--file", default="evals/questions.json")
    ap.add_argument("--only", nargs="*", help="case ids to run")
    ap.add_argument("--resume", metavar="DIR|latest", help="continue an existing run directory")
    ap.add_argument("--no-retry-infra", action="store_true", help="on resume, keep INCONCLUSIVE-infra cases as they are")
    ap.add_argument("--report", metavar="DIR", help="only rebuild reports for a run directory (no network)")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit (no network, no cost)")
    ap.add_argument("--workers", type=int, default=1, help="parallel cases (still capped by the MCP rate limiter)")
    ap.add_argument("--max-consecutive-infra", type=int, default=2, help="circuit breaker threshold")
    ap.add_argument("--max-cost", type=float, default=2.0, help="stop when this invocation spends more (USD)")
    return ap.parse_args(argv)


def _resolve_dir(arg: str, mode: str | None) -> Path:
    if arg == "latest":
        d = latest_run(REPORTS, mode)
        if d is None:
            raise ResumeMismatchError("no previous run found under reports/")
        return d
    d = Path(arg)
    return d if d.is_absolute() else ROOT / d


def main(argv=None) -> int:
    args = _parse(argv)
    try:
        cases, cross = load_cases(ROOT / args.file)
        all_cases = cases
        if args.only:
            unknown = set(args.only) - {q["id"] for q in cases}
            if unknown:
                raise CaseFileError(f"unknown case ids: {sorted(unknown)}")
            cases = [q for q in cases if q["id"] in set(args.only)]
        settings = replace(load_settings(require_key=not (args.dry_run or args.report)), guardrails=args.mode)
        if args.workers < 1:
            raise ConfigError("--workers must be >= 1")
    except (CaseFileError, ConfigError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    # ---------------------------------------------------------------- rebuild reports only
    if args.report:
        store = RunStore(_resolve_dir(args.report, None))
        header = store.read_header()
        if header is None:
            print(f"error: {store.dir} is not a run directory", file=sys.stderr)
            return 1
        records = store.load()
        state = "complete" if not store.pending(all_cases) else "partial"
        write_reports(store.dir, header, all_cases, cross, records, run_state={"state": state})
        print(f"reports rebuilt in {store.dir.relative_to(ROOT)} ({state})")
        return 0

    try:
        run_dir = _resolve_dir(args.resume, args.mode) if args.resume else None
    except ResumeMismatchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.dry_run:
        todo = RunStore(run_dir).pending(cases, not args.no_retry_infra) if run_dir else cases
        print(_plan(cases, todo, settings, run_dir))
        return 0

    # ---------------------------------------------------------------- live run
    limiter = build_limiter(settings)
    try:
        server, tools = asyncio.run(_fetch_catalog(settings, limiter))  # paced like every other session
    except Exception as e:
        print(f"error: MCP server unreachable or catalog invalid ({type(e).__name__}: {e}); nothing was run",
              file=sys.stderr)
        return 3
    header = {"started_utc": _now(), "mode": args.mode, "model": settings.llm_model,
              "temperature": settings.temperature,
              "prompt_sha": hashlib.sha256(prompts.system_prompt(args.mode).encode()).hexdigest()[:12],
              "mcp_url": settings.mcp_url, "server": server, "git": _git_sha(), "questions_file": args.file,
              "rate_limit": {"max_requests": settings.mcp_max_requests, "window_s": settings.mcp_window_s}}
    run_dir = run_dir or REPORTS / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{args.mode}"

    try:
        with RunStore(run_dir) as store:
            if args.resume:
                for w in store.check_resumable(header):
                    print(f"warning: {w}")
                old = store.read_header()
                old.setdefault("resumes", []).append({"at": header["started_utc"], "git": header["git"],
                                                      "server": server})
                header = old
            store.write_header(header)
            return _execute(args, settings, limiter, tools, cases, all_cases, cross, store, header)
    except RunLockedError as e:
        print(f"error: {e}", file=sys.stderr)
        return 4
    except ResumeMismatchError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def _execute(args, settings, limiter, tools, cases, all_cases, cross, store, header) -> int:
    """Run the pending subset of `cases`; reports always cover the whole case file (`all_cases`)."""
    done_before = store.load()
    todo = store.pending(cases, not args.no_retry_infra)
    rel = store.dir.relative_to(ROOT)
    print(f"run -> {rel}  ({header['server']})")
    print(_plan(cases, todo, settings, store.dir if args.resume else None))

    agents = []
    for _ in range(min(args.workers, max(len(todo), 1))):
        a = build_agent(settings, limiter=limiter)
        a.prime_catalog(tools)  # no extra tools/list per worker
        agents.append(a)

    stop = threading.Event()
    state, spent, infra_streak, finished = "complete", 0.0, 0, 0

    def record(rec: dict) -> None:
        nonlocal spent, infra_streak, finished, state
        store.append(rec)
        finished += 1
        spent += _cost(rec)
        infra_streak = infra_streak + 1 if rec["status"] in RETRYABLE else 0
        tools_used = ",".join(c["tool"] for t in rec["turns"] for c in t["trace"]) or "-"
        print(f"  [{finished}/{len(todo)}] {rec['id']:<5} {rec['status']:<19} ${_cost(rec):.4f}  tools={tools_used}",
              flush=True)
        if infra_streak >= args.max_consecutive_infra:
            state = "stopped: circuit breaker"
            print(f"  ! {infra_streak} consecutive infra/internal failures; stopping (protects the server; "
                  "an internal error needs a code fix before resuming)", flush=True)
            stop.set()
        elif spent > args.max_cost:
            state = "stopped: cost limit"
            print(f"  ! spent ${spent:.4f} > --max-cost {args.max_cost}; stopping", flush=True)
            stop.set()

    def attempt_no(q):
        return done_before.get(q["id"], {}).get("attempt", 0) + 1

    try:
        if len(agents) <= 1:
            for q in todo:
                if stop.is_set():
                    break
                record(run_case(agents[0], q, limiter, attempt_no(q)))
        else:
            idle, queue, running = list(agents), list(todo), {}
            pool = ThreadPoolExecutor(max_workers=len(agents))
            try:
                while (queue and not stop.is_set()) or running:
                    while idle and queue and not stop.is_set():
                        q, a = queue.pop(0), idle.pop()
                        running[pool.submit(run_case, a, q, limiter, attempt_no(q))] = a
                    try:
                        fin, _ = wait(running, return_when=FIRST_COMPLETED)
                    except KeyboardInterrupt:
                        if state == "interrupted":
                            raise  # second Ctrl-C: abandon in-flight cases
                        state = "interrupted"
                        stop.set()
                        print(f"\n  interrupted: finishing {len(running)} in-flight case(s) so they are saved; "
                              "Ctrl-C again to abandon them", flush=True)
                        continue
                    for f in fin:
                        idle.append(running.pop(f))
                        record(f.result())
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
    except KeyboardInterrupt:
        state = "interrupted"
        stop.set()
        print("\n  interrupted: finished cases are saved; any case in flight will re-run on resume", flush=True)

    records = store.load()
    remaining = store.pending(cases, not args.no_retry_infra)
    if state == "complete" and remaining:
        state = "partial"  # e.g. cases that ended INCONCLUSIVE-infra in this invocation
    overall = "complete" if not store.pending(all_cases, not args.no_retry_infra) else \
        ("partial" if state == "complete" else state)
    write_reports(store.dir, header, all_cases, cross, records, limiter.snapshot(), {"state": overall})
    status_of = lambda q: records.get(q["id"], {}).get("status")
    infra = sum(1 for q in all_cases if status_of(q) == INCONCLUSIVE_INFRA)
    internal = sum(1 for q in all_cases if status_of(q) == ERROR_INTERNAL)
    print(f"{state}: {len(records)}/{len(all_cases)} recorded · {infra} infra-inconclusive · {internal} internal-error · "
          f"${spent:.4f} this invocation · limiter {limiter.snapshot()}")
    if remaining:
        only = f" --only {' '.join(args.only)}" if args.only else ""
        print(f"resume with: python -m app.evaluation.runner --mode {args.mode} --file {args.file}"
              f" --resume {rel}{only}")
    if state == "interrupted":
        sys.stdout.flush()
        os._exit(130)  # don't wait on in-flight worker threads
    return 0 if state == "complete" else 2


if __name__ == "__main__":
    sys.exit(main())
