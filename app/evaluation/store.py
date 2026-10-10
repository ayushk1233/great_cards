"""Durable, resumable run directory.

reports/<UTC-ts>_<mode>/
  run.json        header: model, mode, prompt sha, case file, server/catalog (written once)
  results.jsonl   one record per *finished* case attempt, appended + fsync'd; last record per id wins
  run.lock        exclusive lock while a runner owns the directory

A case is atomic: it's written only after all its turns finish, so a crash mid-case simply
re-runs that case on resume. A truncated last line (crash during a write) is ignored.
"""

import fcntl
import json
import os
from pathlib import Path

from app.evaluation.checks import RETRYABLE

# header fields that must match for a resume to be valid (results would not be comparable)
RESUME_KEYS = ("mode", "model", "temperature", "prompt_sha", "questions_file")


class RunLockedError(RuntimeError):
    pass


class ResumeMismatchError(RuntimeError):
    pass


class RunStore:
    def __init__(self, run_dir: Path):
        self.dir = Path(run_dir)
        self.results_path = self.dir / "results.jsonl"
        self.header_path = self.dir / "run.json"
        self._lock_fd = None

    # ------------------------------------------------------------------ lifecycle
    def __enter__(self) -> "RunStore":
        self.dir.mkdir(parents=True, exist_ok=True)
        self._lock_fd = os.open(self.dir / "run.lock", os.O_RDWR | os.O_CREAT, 0o644)
        try:
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(self._lock_fd)
            raise RunLockedError(f"another runner is using {self.dir}") from None
        return self

    def __exit__(self, *exc) -> None:
        if self._lock_fd is not None:
            fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
            os.close(self._lock_fd)
            self._lock_fd = None

    # ------------------------------------------------------------------ header
    def read_header(self) -> dict | None:
        return json.loads(self.header_path.read_text()) if self.header_path.exists() else None

    def write_header(self, header: dict) -> None:
        tmp = self.header_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(header, indent=2, ensure_ascii=False))
        os.replace(tmp, self.header_path)

    def check_resumable(self, header: dict) -> list[str]:
        """Raise if the stored run isn't comparable; return warnings for softer drift."""
        old = self.read_header()
        if old is None:
            raise ResumeMismatchError(f"{self.dir} has no run.json; not a run directory")
        diffs = [f"{k}: {old.get(k)!r} -> {header.get(k)!r}" for k in RESUME_KEYS if old.get(k) != header.get(k)]
        if diffs:
            raise ResumeMismatchError("cannot resume, settings differ from the original run:\n  " + "\n  ".join(diffs))
        warnings = []
        if old.get("server", {}).get("catalog_sha256_12") != header.get("server", {}).get("catalog_sha256_12"):
            warnings.append("MCP tool catalog changed since this run started; results before/after may differ")
        if old.get("git") != header.get("git"):
            warnings.append(f"code changed since this run started ({old.get('git')} -> {header.get('git')})")
        return warnings

    # ------------------------------------------------------------------ results
    def load(self) -> dict[str, dict]:
        """Latest record per case id."""
        latest: dict[str, dict] = {}
        if not self.results_path.exists():
            return latest
        for line in self.results_path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # torn final write from a crash
            if "id" in rec:
                latest[rec["id"]] = rec
        return latest

    def append(self, record: dict) -> None:
        line = json.dumps(record, ensure_ascii=False) + "\n"
        # make sure we start on a fresh line even if the previous write was torn
        needs_nl = False
        if self.results_path.exists() and self.results_path.stat().st_size > 0:
            with self.results_path.open("rb") as fh:
                fh.seek(-1, os.SEEK_END)
                needs_nl = fh.read(1) != b"\n"
        with self.results_path.open("a") as fh:
            if needs_nl:
                fh.write("\n")
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())

    def pending(self, cases: list[dict], retry_infra: bool = True) -> list[dict]:
        """Cases still to run: never run, definition changed, or (optionally) infra/internal errors."""
        done = self.load()
        todo = []
        for q in cases:
            rec = done.get(q["id"])
            if rec is None or rec.get("case_sha") != q["sha"]:
                todo.append(q)
            elif retry_infra and rec.get("status") in RETRYABLE:
                todo.append(q)
        return todo


def latest_run(reports_dir: Path, mode: str | None = None) -> Path | None:
    runs = sorted(p for p in Path(reports_dir).glob("*_*") if (p / "run.json").exists()
                  and (mode is None or p.name.endswith(f"_{mode}")))
    return runs[-1] if runs else None
