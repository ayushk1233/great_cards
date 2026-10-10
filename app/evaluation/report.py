"""Reports, regenerated from run.json + results.jsonl (never hand-edited, except review.md).

  transcripts.md  unedited conversations with every tool call, args and raw result
  summary.md      status per case, flags, usage, rate-limiter stats, cross-checks
  tools.md        per-tool rollup: calls, errors by kind, latency, payload size, cases
  review.md       human review template (created once; never overwritten once it exists)
"""

import json
from collections import defaultdict
from pathlib import Path

from app.evaluation.checks import ERROR_INTERNAL, FAIL_AUTO, HARD, INCONCLUSIVE_INFRA, INFO, INFRA, INTERNAL, NEEDS_REVIEW


def _esc(s: str) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def _calls(rec: dict):
    for n, t in enumerate(rec.get("turns", []), 1):
        for c in t.get("trace", []):
            yield n, c


# ------------------------------------------------------------------ cross-checks
def _top_cards(rec: dict | None, turn: int, n: int) -> list[str] | None:
    if not rec or len(rec.get("turns", [])) < turn:
        return None
    for c in reversed(rec["turns"][turn - 1]["trace"]):
        if c["tool"] == "recommend_cards" and c["ok"]:
            try:
                recs = json.loads(c["raw_text"]).get("recommendations", [])
            except (TypeError, json.JSONDecodeError, AttributeError):
                return None
            return [r.get("card_name") for r in recs[:n]]
    return None


def cross_check_results(cross: list[dict], records: dict[str, dict]) -> list[dict]:
    out = []
    for x in cross:
        if x["type"] == "review":
            out.append({**x, "result": "REVIEW"})
            continue
        (qa, ta), (qb, tb) = (r.split("#") for r in (x["a"], x["b"]))
        a, b = _top_cards(records.get(qa), int(ta), x.get("n", 3)), _top_cards(records.get(qb), int(tb), x.get("n", 3))
        result = "INCONCLUSIVE" if a is None or b is None else ("MATCH" if a == b else "MISMATCH")
        out.append({**x, "result": result, "detail": f"{x['a']}: {a} vs {x['b']}: {b}"})
    return out


# ------------------------------------------------------------------ transcripts
def transcripts_md(header: dict, records: list[dict]) -> str:
    out = [f"# Transcripts ({header['mode']}), unedited\n", _header_md(header), "\n---\n"]
    for rec in records:
        out.append(f"## {rec['id']} ({rec.get('category')}): {rec['status']}\n")
        for i, t in enumerate(rec["turns"], 1):
            out.append(f"**User (turn {i}):** {t['user']}\n")
            for c in t["trace"]:
                status = "ok" if c["ok"] else f"{c['error_kind']}: {c['error_msg']}"
                out.append(f"- tool call r{c['round']}: `{c['tool']}` `{json.dumps(c['arguments'], ensure_ascii=False)}` "
                           f"-> {status} ({c['latency_ms']} ms)\n")
                out.append(f"<details><summary>raw result</summary>\n\n```json\n{c['raw_text'] or ''}\n```\n</details>\n")
            if t.get("first_answer") is not None:
                out.append(f"**Assistant (first attempt, rejected by guardrails):**\n\n{t['first_answer']}\n")
            out.append(f"**Assistant:**\n\n{t['answer']}\n")
            flags = ", ".join(f"{f['kind']}:{f['code']}" + (f" ({f['detail']})" if f['detail'] else "") for f in t["flags"])
            out.append(f"_flags: {flags or 'none'} · rounds {t['rounds']} · {t['latency_ms']} ms_\n")
        out.append("\n---\n")
    return "\n".join(out)


# ------------------------------------------------------------------ tool rollup
def tools_md(records: list[dict]) -> str:
    agg = defaultdict(lambda: {"calls": 0, "ok": 0, "errors": defaultdict(int), "lat": [], "chars": [], "cases": set(),
                               "bad_keys": 0})
    for rec in records:
        for n, t in enumerate(rec["turns"], 1):
            bad = {f["detail"].split(".")[0] for f in t["flags"] if f["code"] == "unknown_arg_key"}
            for c in t["trace"]:
                a = agg[c["tool"]]
                a["calls"] += 1
                a["ok"] += c["ok"]
                if not c["ok"]:
                    a["errors"][c["error_kind"]] += 1
                a["lat"].append(c["latency_ms"])
                a["chars"].append(len(c["raw_text"] or ""))
                a["cases"].add(rec["id"])
                a["bad_keys"] += c["tool"] in bad
    rows = ["| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |",
            "|---|---|---|---|---|---|---|---|"]
    for tool in sorted(agg):
        a = agg[tool]
        errs = ", ".join(f"{k} {v}" for k, v in sorted(a["errors"].items())) or "—"
        lat = f"{sum(a['lat']) // len(a['lat'])} / {max(a['lat'])}"
        rows.append(f"| {tool} | {a['calls']} | {a['ok']} | {errs} | {lat} | {sum(a['chars']) // len(a['chars']):,} | "
                    f"{a['bad_keys']} | {', '.join(sorted(a['cases']))} |")
    core = ["get_advisor_context", "recommend_cards", "get_card_details", "list_cards", "compare_cards", "check_eligibility"]
    missing = [t for t in core if t not in agg]
    note = f"\n**Core tools never called in this run:** {', '.join(missing)}\n" if missing else ""
    return ("# Per-tool rollup\n\nFrom the execution traces. Diagnosis questions per tool (D-codes) are in "
            "evals/CASES.md section 2.\n\n" + "\n".join(rows) + "\n" + note)


# ------------------------------------------------------------------ summary
def summary_md(header: dict, records: list[dict], cross: list[dict], limiter: dict | None, run_state: dict) -> str:
    counts = defaultdict(int)
    for r in records:
        counts[r["status"]] += 1
    rows = ["| id | category | status | hard flags | info | tools called |", "|---|---|---|---|---|---|"]
    for r in records:
        fl = [(n, f) for n, t in enumerate(r["turns"], 1) for f in t["flags"]]
        multi = len(r["turns"]) > 1
        fmt = lambda n, f: (f"t{n}:" if multi else "") + f["code"] + (f" ({_esc(f['detail'])[:90]})" if f["detail"] else "")
        hard = "<br>".join(fmt(n, f) for n, f in fl if f["kind"] in (HARD, INFRA, INTERNAL)) or "—"
        info = "<br>".join(fmt(n, f) for n, f in fl if f["kind"] == INFO) or "—"
        tools = ", ".join(c["tool"] for _, c in _calls(r)) or "—"
        rows.append(f"| {r['id']} | {r.get('category')} | **{r['status']}** | {hard} | {info} | {tools} |")
    usage = {k: sum(t.get("usage", {}).get(k, 0) for r in records for t in r["turns"])
             for k in ("llm_calls", "prompt_tokens", "completion_tokens", "cost")}
    mcp_calls = sum(1 for r in records for _ in _calls(r))
    xrows = ["| id | check | result | detail |", "|---|---|---|---|"] + [
        f"| {x['id']} | {x['type']} | {x['result']} | {_esc(x.get('detail', ''))} |" for x in cross]
    lim = (f"**MCP pacing:** {limiter['requests']} HTTP requests this process, {limiter['waited_s']} s waited, "
           f"{limiter['throttled_429']} × 429 · budget {limiter['max_requests']} / {limiter['window_s']:.0f} s\n\n"
           if limiter else "")
    return (
        f"# Eval summary ({header['mode']})\n\n{_header_md(header)}\n\n"
        f"**Run state:** {run_state.get('state')} · {len(records)}/{run_state.get('total')} cases recorded\n\n"
        f"**Status:** {counts[NEEDS_REVIEW]} NEEDS-REVIEW · {counts[FAIL_AUTO]} FAIL-auto · "
        f"{counts[INCONCLUSIVE_INFRA]} INCONCLUSIVE-infra · {counts[ERROR_INTERNAL]} ERROR-internal\n\n"
        "No case passes automatically. NEEDS-REVIEW means every hard check passed; a reviewer still has to "
        "verify the answer against the raw tool output (review.md). INCONCLUSIVE-infra is not a product "
        "failure: resume the run to retry it. ERROR-internal is a bug in our pipeline code (traceback in "
        "transcripts.md): fix it, then resume.\n\n"
        f"**Usage:** {usage['llm_calls']} LLM calls, {usage['prompt_tokens']:,} prompt + {usage['completion_tokens']:,} "
        f"completion tokens, ${usage['cost']:.4f} (OpenRouter-reported) · {mcp_calls} MCP tool calls\n\n"
        + lim + "\n".join(rows) + "\n\n## Cross-case checks\n\n" + "\n".join(xrows) + "\n"
    )


# ------------------------------------------------------------------ review template
def review_md(header: dict, cases: list[dict], records: dict[str, dict]) -> str:
    out = [f"# Human review ({header['mode']} run)\n",
           "Fill in one block per case from transcripts.md. Final status is PASS / FAIL / INCONCLUSIVE "
           "(review); a case never passes on 'sounds reasonable'. Bucket for every failure: Model, MCP tool "
           "or Data, with evidence (raw tool output, tool description or the card's own terms).\n"]
    for q in cases:
        rec = records.get(q["id"], {})
        hard = [f"t{n}:{f['code']} {f['detail']}".strip() for n, t in enumerate(rec.get("turns", []), 1)
                for f in t["flags"] if f["kind"] in (HARD, INFRA, INTERNAL)]
        out.append(f"## {q['id']}: {q.get('title', '')}\n")
        out.append(f"- Auto status: **{rec.get('status', 'not run')}**  ·  severity if failed: {q.get('severity', '?')}"
                   f"  ·  diagnoses: {', '.join(q.get('diagnoses', [])) or '—'}")
        out.append(f"- Hard flags: {'; '.join(hard) or 'none'}")
        out.append("- Review checklist:")
        out += [f"  - [ ] {item}" for item in q.get("review", [])] or ["  - [ ] answer matches raw tool output"]
        out += ["- **Final status:** ", "- **Severity:** ", "- **Bucket (Model / MCP tool / Data):** ",
                "- **Evidence:** ", "- **Open questions:** ", ""]
    return "\n".join(out)


def _header_md(h: dict) -> str:
    keys = ("started_utc", "mode", "model", "temperature", "prompt_sha", "mcp_url", "server", "git", "questions_file")
    return "\n".join(f"- **{k}**: `{h.get(k)}`" for k in keys if k in h)


def write_reports(run_dir: Path, header: dict, cases: list[dict], cross: list[dict], records: dict[str, dict],
                  limiter: dict | None = None, run_state: dict | None = None) -> None:
    ordered = [records[q["id"]] for q in cases if q["id"] in records]
    xres = cross_check_results(cross, records)
    run_state = {"total": len(cases), **(run_state or {})}
    (run_dir / "transcripts.md").write_text(transcripts_md(header, ordered))
    (run_dir / "summary.md").write_text(summary_md(header, ordered, xres, limiter, run_state))
    (run_dir / "tools.md").write_text(tools_md(ordered))
    review = run_dir / "review.md"
    # created once the run is complete; after that it holds human edits and is never overwritten
    if run_state.get("state") == "complete" and not review.exists():
        review.write_text(review_md(header, cases, records))
