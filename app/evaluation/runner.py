"""Reproducible evaluation run.

    python -m app.evaluation.runner --mode off                    # all of evals/questions.json
    python -m app.evaluation.runner --mode on --only Q03 Q07
    python -m app.evaluation.runner --file evals/smoke.json

Sequential, fresh conversation per question, pause between questions (production server).
Writes reports/<UTC-ts>_<mode>/ : results.jsonl, transcripts.md (unedited), summary.md.
"""

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from app.agent.orchestrator import Agent, TurnResult, build_agent
from app.config import ROOT, load_settings
from app.evaluation.checks import run_checks
from app.mcp.client import McpSession
from app.mcp.tools import build_tool_specs

PAUSE_S = 3.0


def _git_sha() -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()
        return sha + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


async def _server_header(url: str) -> dict:
    async with McpSession(url) as s:
        specs = build_tool_specs(await s.list_tools())
    digest = hashlib.sha256(json.dumps(specs, sort_keys=True).encode()).hexdigest()[:12]
    return {**s.server_info, "catalog_sha256_12": digest}


def _trace_json(r: TurnResult) -> list[dict]:
    return [{"round": t.round, "tool": t.tool, "arguments": t.arguments, "ok": t.result.ok,
             "error_kind": t.result.error_kind, "error_msg": t.result.error_msg,
             "latency_ms": t.result.latency_ms, "raw_text": t.result.raw_text} for t in r.trace]


def run_question(agent: Agent, q: dict) -> dict:
    history, turns, flags = [], [], []
    for i, msg in enumerate(q["turns"]):
        r = agent.run_turn(history, msg)
        history = r.history
        turns.append({
            "user": msg, "answer": r.answer, "error": r.error, "error_detail": r.error_detail,
            "trace": _trace_json(r), "validation": r.validation.as_dict(), "rounds": r.rounds,
            "hit_max_rounds": r.hit_max_rounds, "regenerated": r.regenerated, "fell_back": r.fell_back,
            "first_answer": r.first_answer,
            "first_validation": r.first_validation.as_dict() if r.first_validation else None,
            "latency_ms": r.latency_ms, "usage": r.usage,
        })
        flags += [f"t{i + 1}:{f}" for f in run_checks(q, r)] if len(q["turns"]) > 1 else run_checks(q, r)
        if r.error:
            break
    return {"id": q["id"], "category": q.get("category"), "notes": q.get("notes", ""),
            "expectations": q.get("expectations", {}), "turns": turns, "flags": flags}


def _transcript_md(res: dict) -> str:
    out = [f"## {res['id']} ({res['category']})\n"]
    for i, t in enumerate(res["turns"], 1):
        out.append(f"**User (turn {i}):** {t['user']}\n")
        for c in t["trace"]:
            status = "ok" if c["ok"] else f"{c['error_kind']}: {c['error_msg']}"
            out.append(f"- tool call r{c['round']}: `{c['tool']}` `{json.dumps(c['arguments'], ensure_ascii=False)}` "
                       f"-> {status} ({c['latency_ms']} ms)\n")
            out.append(f"<details><summary>raw result</summary>\n\n```json\n{c['raw_text'] or ''}\n```\n</details>\n")
        if t["first_answer"] is not None:
            out.append(f"**Assistant (first attempt, rejected by guardrails):**\n\n{t['first_answer']}\n")
            out.append(f"_violations: {json.dumps(t['first_validation']['violations'], ensure_ascii=False)}_\n")
        out.append(f"**Assistant:**\n\n{t['answer']}\n")
        out.append(f"_validation: {'ok' if t['validation']['ok'] else json.dumps(t['validation']['violations'], ensure_ascii=False)}"
                   f" · rounds {t['rounds']} · {t['latency_ms']} ms_\n")
    return "\n".join(out) + "\n---\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["off", "on"], default="off", help="guardrails report-only (off) or enforced (on)")
    ap.add_argument("--file", default="evals/questions.json")
    ap.add_argument("--only", nargs="*", help="question ids to run")
    args = ap.parse_args(argv)

    questions = json.loads((ROOT / args.file).read_text())["questions"]
    if args.only:
        questions = [q for q in questions if q["id"] in set(args.only)]
    if not questions:
        print(f"no questions to run in {args.file}", file=sys.stderr)
        return 1

    settings = replace(load_settings(), guardrails=args.mode)
    agent = build_agent(settings)
    header = {
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": args.mode, "model": settings.llm_model, "temperature": settings.temperature,
        "mcp_url": settings.mcp_url, "server": asyncio.run(_server_header(settings.mcp_url)),
        "git": _git_sha(), "questions_file": args.file, "n": len(questions),
    }
    out_dir = ROOT / "reports" / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}_{args.mode}"
    out_dir.mkdir(parents=True)
    print(f"run -> {out_dir.relative_to(ROOT)}  ({header['server']})")

    results = []
    with (out_dir / "results.jsonl").open("w") as fh:
        fh.write(json.dumps({"header": header}, ensure_ascii=False) + "\n")
        for i, q in enumerate(questions):
            if i:
                time.sleep(PAUSE_S)
            res = run_question(agent, q)
            results.append(res)
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")
            fh.flush()
            tools = ",".join(c["tool"] for t in res["turns"] for c in t["trace"]) or "-"
            print(f"  {res['id']:<5} {len(res['flags'])} flags  tools={tools}")

    hdr = "\n".join(f"- **{k}**: `{v}`" for k, v in header.items())
    (out_dir / "transcripts.md").write_text(
        f"# Transcripts ({args.mode}) — unedited\n\n{hdr}\n\n---\n\n" + "".join(_transcript_md(r) for r in results))
    rows = ["| id | category | tools called | flags |", "|---|---|---|---|"]
    for r in results:
        tools = ", ".join(c["tool"] for t in r["turns"] for c in t["trace"]) or "—"
        flags = "<br>".join(f.replace("|", "\\|") for f in r["flags"]) or "—"
        rows.append(f"| {r['id']} | {r['category']} | {tools} | {flags} |")
    flagged = sum(1 for r in results if r["flags"])
    tot = {k: sum(t.get("usage", {}).get(k, 0) for r in results for t in r["turns"])
           for k in ("llm_calls", "prompt_tokens", "completion_tokens", "cost")}
    mcp_calls = sum(len(t["trace"]) for r in results for t in r["turns"])
    cost_line = (f"**Usage:** {tot['llm_calls']} LLM calls, {tot['prompt_tokens']:,} prompt + "
                 f"{tot['completion_tokens']:,} completion tokens, ${tot['cost']:.4f} (OpenRouter-reported) · "
                 f"{mcp_calls} MCP tool calls.\n\n")
    (out_dir / "summary.md").write_text(
        f"# Eval summary ({args.mode})\n\n{hdr}\n\n**{flagged}/{len(results)} questions flagged.** "
        "Flags are automatic hints; failure classification (Model / MCP / Data) is in failures.md.\n\n"
        + cost_line
        + "\n".join(rows) + "\n")
    print(f"done: {flagged}/{len(results)} flagged · ${tot['cost']:.4f} · {mcp_calls} MCP calls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
