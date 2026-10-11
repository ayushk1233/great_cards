# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A credit-card advisor chatbot for Indian cards, built on the public Great.cards MCP server (`https://bk-api.bankkaro.com/mcp`, production), plus a 20-case adversarial evaluation. Every failure is classified as **Model / MCP tool / Data**. Model failures are fixed on the chatbot side (prompt rules F1–F5). MCP and data failures are written up for engineering in `reports/engineering_handoff.md`. It was an assignment submission, so `README.md` is the deliverable index.

## Commands

Setup: Python 3.12+ (developed on 3.14), with `.venv` and `pip install -r requirements.txt`. `.env` needs `OPENROUTER_API_KEY` (see `.env.example`). pydantic is pinned to 2.12.x because openrouter and mcp need overlapping ranges, so don't bump it on its own.

```bash
pytest -q                                   # offline tests (no network, no key); `live` marker excluded by pytest.ini
pytest tests/test_validation.py::test_name  # single test
pytest -m live                              # hits the real production MCP server
python -m app.health                        # connectivity check: 1 LLM call + ~3 MCP requests
streamlit run app/ui.py                     # chat UI on :8501
python -m app.evaluation.runner --dry-run   # plan an eval run, no network/cost
python -m app.evaluation.runner --mode prompt [--only Q01 Q05] [--resume latest]
python -m app.evaluation.runner --report reports/<run_dir>   # rebuild reports offline
```

A full eval run makes about 205 MCP requests, takes about 12 minutes because requests are paced, and costs $0.25–0.50. Other runner flags: `--workers`, `--max-cost`, `--max-consecutive-infra` (circuit breaker), `--no-retry-infra`.

## Architecture

- **`app/agent/orchestrator.py` `run_turn()`** is the single entry point. The UI and the eval runner both call it. It runs the LLM ⇄ MCP tool loop, enforces the per-turn limits (`MAX_TOOL_CALLS_PER_TURN`=6, extra calls refused rather than sent; `TURN_DEADLINE_S`=180), then runs validation. It returns the answer, the check results and the full tool trace.
- **Guardrail modes** (`GUARDRAILS` env var / `--mode` / UI sidebar): `off` = baseline prompt, validator reports only. `prompt` = baseline + approved rule blocks, report only (this is the measured "after"). `on` = all rules + one validator-driven rewrite, then a safe fallback. `app/agent/prompts.py` composes `BASELINE` + an addendum per mode, so before/after stays a one-block diff. The `BASELINE` is deliberately plain.
- **`app/agent/validation.py`** holds pure functions checking ₹ grounding (every ₹ figure must appear in a tool result or the user's input), approval promises and tax advice. The known blind spots are pinned as tests in `tests/test_known_weaknesses.py` (W1–W9). The ₹ check only confirms the figure exists *somewhere* in tool output, so human review against raw output stays mandatory.
- **`app/agent/llm.py`** is the only module that imports `openrouter`. It uses temperature 0 with no parallel tool calls, and SDK errors are raised as `LlmError`.
- **`app/mcp/client.py`** normalises every result and error into `ToolResult{ok, data, error_kind, ...}`. Error kinds are `tool_error`, `malformed` and `unavailable`. Errors reach the model as data instead of crashing. Note that the server sometimes returns `{"error"}` with `isError=false`.
- **`app/mcp/tools.py`** holds the allowlisted tools. Their schemas are copied verbatim from the live server (snapshot in `discovery/tools.json`). It raises `MissingToolError` if the server drops one.
- **`app/mcp/ratelimit.py`** is a file-backed limiter (`.cache/mcp_ratelimit.json`) shared across processes by the UI, the runner and health. The server limits at about 65 requests per 3 minutes, and the client paces itself at 50/180 s. Every HTTP request goes through it.
- **`app/evaluation/`**: `runner.py` is resumable and rate-limited. Each run writes `reports/<timestamp>_<mode>/` (`results.jsonl`, `transcripts.md`, `summary.md`, plus a human `review.md`).
- **Server playbook = data.** The server's ~42k-character advisor context is passed to the model as a tool result, not as system instructions, because it asks for figures no tool returns. `RUPEE_RULE` explicitly overrides it.
- **Tests** use a fake LLM, a fake MCP and recorded server responses from `discovery/raw/*.json` (the `raw` fixture in `tests/conftest.py`).

## Rules for this repo

- **Never stress or modify the production MCP server.** It is read-only and every request is paced. Don't add uncontrolled live calls, loops or parallel probes.
- **Eval cases are frozen.** `evals/CASES.md` is the source of truth, and `evals/questions.json` must mirror it (enforced by `tests/test_cases_sync.py`). Never edit a case to make the bot pass. Record any change in the CASES.md change log with a reason.
- **Prompt and rule changes are fixes and need approval.** Propose a change to any prompt block in `app/agent/prompts.py` (or any other fix) and wait for an OK before applying it.
- **Run reports under `reports/<run_dir>/` are unedited records.** Don't hand-edit transcripts or results. `ai_transcript/README.md` is the final submitted transcript, so never regenerate or edit it.
- Card facts in answers must come from tool calls only, never from model memory.
- `PROGRESS.md` and `Great_cards_AI_Product_Intern_Assignment.md` are private, gitignored working docs.
