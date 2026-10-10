"""Load and validate an eval file (evals/questions.json is the machine copy of evals/CASES.md).

Format:
  {"questions": [{"id", "category", "title"?, "severity"?, "diagnoses"?, "review"?: [str],
                  "turns": [str | {"user": str, "expect": {...}}]}],
   "cross_checks"?: [{"id", "type": "same_top_cards", "a": "Q01#1", "b": "Q06#1", "n": 3} |
                     {"id", "type": "review", "detail": str}]}

Legacy `expectations` on a question applies to every turn (kept for evals/smoke.json).
"""

import hashlib
import json
from pathlib import Path

from app.evaluation.checks import EXPECT_KEYS


class CaseFileError(ValueError):
    pass


def _norm_turns(q: dict) -> list[dict]:
    legacy = q.get("expectations") or {}
    out = []
    for t in q.get("turns") or []:
        t = {"user": t} if isinstance(t, str) else dict(t)
        t.setdefault("expect", legacy)
        out.append(t)
    return out


def case_sha(q: dict) -> str:
    """Fingerprint of everything that defines a case; resume re-runs a case whose sha changed."""
    return hashlib.sha256(json.dumps(q, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]


def load_cases(path: Path) -> tuple[list[dict], list[dict]]:
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        raise CaseFileError(f"cannot read {path}: {e}") from None
    questions, seen, problems = [], set(), []
    for i, q in enumerate(doc.get("questions") or []):
        qid = q.get("id")
        if not qid or qid in seen:
            problems.append(f"question #{i}: missing or duplicate id {qid!r}")
            continue
        seen.add(qid)
        turns = _norm_turns(q)
        if not turns or any(not isinstance(t.get("user"), str) or not t["user"].strip() for t in turns):
            problems.append(f"{qid}: every turn needs a non-empty user message")
        for n, t in enumerate(turns, 1):
            unknown = set(t["expect"]) - EXPECT_KEYS
            if unknown:
                problems.append(f"{qid} turn {n}: unknown expectation keys {sorted(unknown)}")
            for want in t["expect"].get("must_call", []):
                if not isinstance(want, dict) or "tool" not in want:
                    problems.append(f"{qid} turn {n}: must_call entries need a 'tool'")
        questions.append({**q, "turns": turns, "sha": case_sha(q)})
    cross = doc.get("cross_checks") or []
    for x in cross:
        if x.get("type") == "same_top_cards":
            for ref in (x.get("a"), x.get("b")):
                qid, _, turn = str(ref).partition("#")
                if qid not in seen or not turn.isdigit():
                    problems.append(f"{x.get('id')}: bad reference {ref!r}")
        elif x.get("type") != "review":
            problems.append(f"{x.get('id')}: unknown cross-check type {x.get('type')!r}")
    if problems:
        raise CaseFileError("invalid case file:\n  " + "\n  ".join(problems))
    if not questions:
        raise CaseFileError(f"no questions in {path}")
    return questions, cross
