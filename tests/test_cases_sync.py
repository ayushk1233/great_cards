"""evals/questions.json must match evals/CASES.md (the source of truth): same ids, same user
messages in the same order, same severity. Guards against silently editing a question."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _cases_md() -> dict[str, dict]:
    text = (ROOT / "evals" / "CASES.md").read_text()
    blocks = re.split(r"^#### ", text, flags=re.M)[1:]
    out = {}
    for b in blocks:
        m = re.match(r"(Q\d{2}):", b)
        if not m:
            continue
        b = b.split("\n### ")[0].split("\n## ")[0]
        inputs = re.findall(r"\*\*(?:Input|Turn \d+):\*\* `([^`]+)`", b)
        sev = re.search(r"\*\*Severity if failed:\*\* (S\d)", b)
        out[m.group(1)] = {"turns": inputs, "severity": sev.group(1) if sev else None}
    return out


def test_questions_json_matches_cases_md():
    md = _cases_md()
    js = {q["id"]: q for q in json.loads((ROOT / "evals" / "questions.json").read_text())["questions"]}
    assert list(md) == list(js) and len(md) == 20
    for qid, spec in md.items():
        users = [t["user"] if isinstance(t, dict) else t for t in js[qid]["turns"]]
        assert users == spec["turns"], qid
        assert js[qid]["severity"] == spec["severity"], qid
