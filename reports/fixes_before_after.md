# Before and after: every fix, and what it changed

This document records every change made to the chatbot side and its effect on the same 20 sceptical cases. The MCP server was never modified. What's left after these fixes is mostly server/data defects, which go to engineering (see [failures.md](failures.md)).

## Runs compared

| | Before (baseline) | Intermediate | **After (final)** |
|---|---|---|---|
| Run | [`20261010T230941Z_off`](20261010T230941Z_off/review.md) | [`20261011T002732Z_prompt`](20261011T002732Z_prompt/review.md) | [`20261011T005033Z_prompt`](20261011T005033Z_prompt/review.md) |
| Prompt | BASELINE only | + F1, F2, F3 | + F1, F2, F3, F4, F5 |
| Prompt sha | `2f7726b5dcad` | `3edd1401d9d0` | `40a5f4cb6078` |
| Server / catalog / model / temp | 1.6.1 / `0600faf19c22` / claude-haiku-5.5 / 0 | same | same |
| Cost / LLM calls / MCP requests / 429s | $0.27 / 89 / 207 / 0 | $0.27 / 85 / 204 / 0 | $0.49 / 90 / 207 / 0 |

All three runs use the identical case file (`evals/questions.json`, unchanged). Every verdict is a manual review against the raw tool output. The automatic checker is only a first pass: it has known false positives (sums of the user's own amounts) and misses (coincidental matches).

## The fixes

### Answer-side fixes (prompt rules, `GUARDRAILS=prompt`; [`app/agent/prompts.py`](../app/agent/prompts.py))

| # | Fix | Problem it targets | Rule, in short |
|---|---|---|---|
| F1 | `RUPEE_RULE` | E04: ₹ figures no tool returned (break-even months, net-after-fee, "corrected" values, cap arithmetic) | Show only ₹ amounts a tool returned, or the user's own amounts restated per month or per year. No totals, differences, net-after-fee or payback figures, even when tool or playbook text asks for them. If a figure is missing, say so and show the returned parts. If a figure contradicts the terms, say so and quote the terms, without replacing it with an invented number. |
| F2 | `MONTHLY_FIELD_NOTE` | E07: `top_spend_categories[].annual_value` holds monthly values; the bot read it as yearly, or doubted the correct yearly total | States the server fact: present that field per month, and use `annual_rewards_value` / `net_annual_savings` for yearly figures. The bot may still say the field is mislabelled (the defect stays visible). |
| F3 | Point × value clause in F1 | Q07 residual: "12,000 points × ₹0.25 = ₹3,000" in 3 of 3 samples | Converting points to rupees counts as a calculation. Quote the points and the point value as stated. |
| F4 | `FEE_RULE` | Fee/waiver misreads: joining and annual fee merged, a waiver moved to the joining fee, the model judging waiver thresholds itself | Quote the joining and annual fee from their own fields. A waiver applies only to the fee whose field states it. Whether the user's spend earns a waiver comes from `annual_fee_waived` (server behaviour verified across every recorded output), never the model's own threshold check. If no field settles it, say the tools don't confirm it. |
| F5 | Anti-overfitting pass | Rule examples that reused eval-case numbers | All examples use neutral numbers (₹12,000/month, ₹500 vs ₹6,000, 5,000 points at ₹0.50). A test fails if any eval card name or case figure appears in the rule text. |

**How we avoided overfitting to these 20 cases.**
- **No case content in the rules.** They refer only to tool field names and general behaviour (quote, don't compute; say when the tools don't confirm something). They contain no card names, case figures or per-question instructions. `test_system_prompt_modes` enforces this.
- **Grounding points the other way.** Every rule pushes the bot towards stating less and attributing more: quote returned fields, otherwise say "the tools don't provide it". None of the rules tells the bot what the right answer is.
- **The case file wasn't changed.** No expectations were added to `evals/questions.json` during the fix cycle.
- **Residual risk:** F2 and F4 encode *current* server behaviour (field labels, waiver flag). If engineering fixes those fields, both rules must be revisited, and F2 deleted once `annual_value` is really annual. With 20 cases and one sample each, the results show direction; they don't prove generalisation.

### Infrastructure fixes (before the baseline; they don't change what the bot says)

| Fix | Why |
|---|---|
| Rate limiter on every MCP HTTP request (50 per 180 s, 0.5 s gap, shared 429 cooldown, file-backed) | Production server limits at about 65 per 3 min; 0 × 429 across all runs |
| Waits before each request, outside the SDK read timeout | Rate-limit waits were being counted as timeouts |
| Per-turn tool-call budget (6) and 180 s turn deadline | Runaway tool loops and hung turns |
| Internal errors kept separate from infrastructure errors | Our bugs are never counted as product failures, and vice versa |
| Tool catalog cached per agent | Repeated tools/list calls (W14) |
| Validator tuning: 2 detector false positives removed | Tax label and "can't confirm" refusals were flagged wrongly |

### Considered but not applied

- **Approval and tax rules** (in `GUARDRAILS=on`): the S1 cases (Q15, Q19) passed in both prompt-mode runs without them. They stay available for the guardrails task, unmeasured here.
- **Validator-driven rewrite** (`GUARDRAILS=on`): untested live. The remaining issues are mostly ones the validator can't see.

## Results

| | Before | Intermediate | **After** |
|---|---|---|---|
| PASS / FAIL | 6 / 14 | 12 / 8 | **11 / 9** |
| S1 (most harmful) | 2 (Q15, Q19) | 0 | **0** |
| S2 | 9 | 4 | 5 |
| S3 | 3 | 4 | 4 |
| Cases with ₹ figures no tool returned | 6 (Q05, Q07, Q09, Q11, Q13, Q20) | 0 | **0** |
| Fee/waiver misstatements | 1 (Q01) | 2 (Q13, Q15) | 1 (Q01) |

### Per case

| id | Before | Intermediate | After | Main reason for final verdict |
|---|---|---|---|---|
| Q01 | FAIL S2 | FAIL S3 | FAIL S2 | Swiggy Ornge waiver contradicts the tool's `annual_fee_waived: true` (Model, F4 not followed); no Prime caveat |
| Q02 | FAIL S2 | FAIL S3 | FAIL S3 | Asks for a second category (server playbook "MINIMUM REQUIRED", E14) |
| Q03 | PASS | PASS | PASS | — |
| Q04 | FAIL S2 | FAIL S2 | FAIL S2 | Milestone overvaluation ranks a card #1 (server C1/E03) |
| Q05 | FAIL S2 | FAIL S3 | FAIL S3 | Asks for more categories (E14) |
| Q06 | FAIL S2 | FAIL S2 | FAIL S2 | Online-only dining credited for in-person dining (server C4/E05); milestone uncaveated |
| Q07 | FAIL S2 | PASS | PASS | — |
| Q08 | FAIL S3 | FAIL S3 | FAIL S3 | Lounge visits labelled per quarter (server E10) |
| Q09 | FAIL S2 | PASS | FAIL S3 | Same lounge label passed on for a #2 card (server E10) |
| Q10 | PASS | PASS | PASS | — |
| Q11 | FAIL S3 | PASS | PASS | — |
| Q12 | PASS | PASS | PASS | — |
| Q13 | FAIL S2 | FAIL S2 | FAIL S2 | In-person dining credited at 5% with no caveat (server C4/E05); silent Magnus choice |
| Q14 | PASS | PASS | PASS | — (costly: paged all 258 cards) |
| Q15 | FAIL **S1** | FAIL S2 | PASS | — (tool's "eligible" now contradicted with the card's ₹18 LPA term) |
| Q16 | FAIL S3 | PASS | FAIL S2 | Regalia Gold listed as eligible at ₹6 lakh (server E01 passed through); no indicative caveat |
| Q17 | PASS | PASS | PASS | — |
| Q18 | PASS | PASS | PASS | — |
| Q19 | FAIL **S1** | PASS (borderline) | PASS | — |
| Q20 | FAIL S2 | PASS | PASS | — |

## What the fixes achieved, and what they didn't

**Achieved (consistent across both after-runs):**
- **Calculated ₹ figures: 6 cases → 0 → 0** (F1, F3). The bot now says "the tools don't provide it" and lists the returned parts. Server defects stay visible: E06 (joining fee left out of net), E03 (milestone contradicts the terms), E01 (eligibility contradicts the terms).
- **Monthly field read correctly** in every answer that uses it (F2).
- **Pass rate 6 → 12 → 11; S1 2 → 0 → 0.** Q15 and Q19 improved although the approval and tax rules weren't applied. That's likely the general "quote the terms when a figure contradicts them" behaviour, but with one sample per run this isn't proven.

**Not achieved:**
- **Fee/waiver errors aren't eliminated** (1 → 2 → 1). F4 removed the Q13 and Q15 errors, but Q01 still overrode the waiver flag with its own threshold check. A prompt rule lowers the rate; it doesn't guarantee the behaviour.
- **Run-to-run variation is large:** Q09 and Q16 flipped between runs for reasons unrelated to any fix (the lounge label, a dropped caveat). The final run's 11 vs the intermediate's 12 is within that noise.
- **Cost went up** ($0.27 → $0.49). Most of it is Q14 ($0.26), which paged the whole catalogue to filter free cards because `list_cards` ignores the filter. It's more thorough, but expensive. Whether F4 encouraged this isn't established.

**Remaining failures by root cause (final run):**

| Root cause | Cases | Owner |
|---|---|---|
| Milestone overvaluation (E03/C1) | Q04, Q06 | **Server**: engineering spec |
| Online-only dining credited for in-person spend (E05/C4) | Q06, Q13 | **Server / data** |
| Lounge `*_per_quarter` holds annual visits (E10) | Q08, Q09 | **Server** |
| Eligibility ignores income floors (E01) | Q16 (and the root of Q15) | **Server**: engineering spec |
| Playbook requires 2 categories before ranking (E14) | Q02, Q05, Q06 T1 | **Server** guidance text |
| Waiver threshold judged by the model (F4 not followed) | Q01 | Model (residual) |

Nine failures remain. Every one except Q01 traces back to a server-side field, calculation or guidance defect. The chatbot can surface those defects, but it can't correct them without inventing numbers.

## Reproduce

```bash
python -m app.evaluation.runner --mode off      # before
python -m app.evaluation.runner --mode prompt   # after
```

About 205 MCP requests per full run (rate-limited, about 12 min); $0.25–0.50 in OpenRouter usage. Offline tests: `pytest -q` (108 passed, 12 xfailed).
