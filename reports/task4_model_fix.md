# Task 4: model-side fix for E04 (₹ figures no tool returned)

**Status:** applied in `GUARDRAILS=prompt` mode, measured on 9 cases (one sample each, before and after).

**Result:** the fix worked on 3 of the 4 cases that could be measured. It reduced the failure but didn't eliminate it on the fourth (Q07), and the 5th and 6th target cases couldn't be measured. There are two side effects: Q09 asked follow-up questions instead of answering, and Q07/Q20 now doubt a correct figure. Details below.

## 1. Why this failure is model-side

The [baseline review](failures.md#e04--figures-the-tools-didnt-return-s2-mixed-model--mcp-guidance) found calculated or invented ₹ figures in 6 of 20 cases. For every figure listed there, the raw tool output for that turn doesn't contain it. The tools returned correct inputs and the LLM did its own arithmetic.

One case was an outright invention: Q09's baseline "typical card 1.5–3.5%" isn't anywhere in the tool data.

A contributing cause is the server playbook, which the bot loads on every turn. It tells the model to say "Your savings of ₹Y more than cover this in [Z] months" (`discovery/raw/context__advisor_full.json`). Our baseline prompt had no rule to override it. **Fixing this on the model side is the right layer** because the server returned correct figures; the only bad numbers came from the model.

## 2. The change (smallest effective)

- **New mode `GUARDRAILS=prompt`:** one rule block (`RUPEE_RULE`) is appended to the unchanged baseline prompt. The validator still only reports and nothing is rewritten, so before/after isolates the prompt.
- **`RUPEE_RULE`** ([`app/agent/prompts.py`](../app/agent/prompts.py)):
  - **Allows:** returned figures, and the user's own amounts restated per month or per year.
  - **Forbids:** totals, differences, net-after-fee figures, caps applied to spend, break-even periods and "corrected" values. This applies *even if tool or context text asks for one*.
  - **When the user asks for an unreturned figure:** say so, show the returned components, and say what each includes or leaves out.
  - **When a returned figure contradicts the card terms:** say so and quote the terms, without replacing the figure with the bot's own number. This keeps server defects visible instead of hidden.
- **Other changes:** `config.py` and `runner.py` accept the new mode, and `.env.example` documents it. The tax and approval rules are **not** bundled in, so they can be measured as separate fixes.
- **Offline tests** ([`tests/test_orchestrator.py`](../tests/test_orchestrator.py)):
  - The rule is in the system prompt only in `prompt` and `on` modes.
  - `prompt` mode never regenerates.
  - The other rules aren't included.
  - Config accepts and rejects the right modes.
- **Suite:** 108 passed, 12 xfailed (known weaknesses), 0 failed.

**Risks identified in advance:**
1. Over-refusal (declining to restate the user's own amounts).
2. Less helpful answers to "break-even" requests.
3. The bot dropping a server defect it currently reports.
4. Run-to-run variation, with only one sample per side.

The results below show which of these happened.

## 3. Runs

| | Before (`off`) | After (`prompt`) |
|---|---|---|
| Run | [`20261010T235127Z_off`](20261010T235127Z_off/transcripts.md) | [`20261010T235631Z_prompt`](20261010T235631Z_prompt/transcripts.md) |
| Prompt sha | `2f7726b5dcad` (= baseline) | changed (logged in `run.json`) |
| Cases | Q20, Q05, Q07, Q09, Q11, Q13 (target); Q01, Q03, Q10 (controls) | same |
| Server, catalog, model, temperature | 1.6.1, `0600faf19c22`, haiku-5.5, 0 | same |
| Cost / MCP requests / 429s / infra errors | $0.135 / 91 / 0 / 0 | $0.118 / 87 / 0 / 0 |

The full transcripts, with every tool request and raw response, are unedited in each run's `transcripts.md` and `results.jsonl`.

## 4. Results (manual review of every answer against its raw tool output)

The automatic ₹ check can't be trusted on its own:
- **False alarms:** it flags sums of the user's own amounts.
- **Misses:** it doesn't catch a figure that appears elsewhere in the tool output by coincidence.

So every ₹ figure below was checked by hand.

| Case | Before: figures no tool returned | After: figures no tool returned | Verdict |
|---|---|---|---|
| **Q20** (original) | T1 "first-year net savings ₹7,820", "break-even in month 2", "₹8,820"; T2 "₹9,000 − ₹1,180 = ₹7,820" | **None.** It says the tools don't return these and lists the returned ₹9,000, ₹1,180, ₹1,180 waiver and ₹1,000 welcome bonus | **Fixed** |
| **Q11** | "about ₹24,000/year back" (its own cap arithmetic) | **None.** It fetched `recommend_cards` top_n=100, where SBI Cashback `net_annual_savings: "₹24,000"` is returned, and cited that | **Fixed** (the right behaviour: get the figure from the tool) |
| **Q13** T2 | "~₹9,600" for SBI (overriding the tool's ₹12,000), "~₹8,400 after fees", "~₹2,900", "about −₹11,900"; recommended Amazon Pay over the tool's #1 | **None** beyond the user's own totals ("₹20,000/month total (₹2.4 lakh/year)"). It keeps the tool's ₹12,000 and explains in words why it may be lower (online-only dining) | **Fixed** |
| **Q07** | T1 "about ₹6,800", "about ₹3,000"; T2 "About ₹2,700 (₹1,518 + ₹3,000 − ₹1,769)", "₹1,100/month", "~₹2.6 lakh" | T1 "at ₹0.25 per point that is about ₹3,000, not ₹30,000" (**still calculated**; the checker missed it because "₹3,000" appears in the fuel-waiver text). T2 retracts it: "My earlier ₹3,000 estimate was my own calculation, not a tool figure, so please disregard it." | **Improved, not fixed** (6 figures → 1, then retracted) |
| **Q09** | "avoids about ₹11,900 in markup compared with a 1.49% card"; "roughly ₹11,900 a year" | **No recommendation given:** it called `list_cards`, then asked 3 clarifying questions | **Not measurable;** possible over-caution (see §5) |
| **Q05** | No `recommend_cards` call (asked for more categories) | Same | **Not measurable in either run** (E14 behaviour, unrelated to this rule) |
| Q03 (control) | Rounded tool figures ("about ₹9,600", "about ₹9,200") | Exact tool figures (₹9,611, ₹9,240); waiver statement still correct | No regression |
| Q10 (control) | Fees, waiver, APR all correct | Same | No regression |
| Q01 (control) | No `recommend_cards` call | Same | Not measurable in either run |

**Turns with at least one figure no tool returned** (the 6 target cases):
- **Before:** 7 turns (Q07 T1, Q07 T2, Q09, Q11, Q13 T2, Q20 T1, Q20 T2).
- **After:** 1 turn (Q07 T1).

### Server defects still surfaced (no hiding)

| Defect | After-run evidence |
|---|---|
| E06 joining fee not in `net_annual_savings` | Q20 T2: "The tool's formula subtracts only the annual fee, not the joining fee. Its result includes this note: 'net_annual_savings = annual_rewards + milestone_benefits + lounge_value - annual_fee.'" |
| E03 milestone overvaluation | Q07 T2: "The card's terms say the milestone is 12,000 bonus points on ₹3 lakh of annual retail spend, and 1 point = ₹0.25. The tool shows ₹30,000, so that figure doesn't match … Treat the ₹30,000 as unverified" |
| E05 online-only dining | Q13 T2: "SBI's 5% dining cashback applies only to restaurant payments made through online platforms. If your ₹5,000 is mostly in-person dining, it would earn 1% offline instead, and the ₹12,000 estimate would be lower." Not raised in the before run's Q13. |

### Q20 transcript, before and after (verbatim, excerpted; full text in each run's transcripts.md)

Tool output (identical in both runs):
- `recommend_cards{amazon_spends:15000}` → HDFC MILLENIA `"net_annual_savings": "₹9,000"`, `"annual_rewards_value": "₹9,000"`, `"joining_fee": "₹1,180 (incl. GST)"`, `"annual_fee": "Free (waived at ₹1,00,000/yr spend; ₹1,180 otherwise)"`, welcome `cash_value: 1000`.
- `_format_hint`: "net_annual_savings = annual_rewards + milestone_benefits + lounge_value - annual_fee".

**Before, T1:**
> **HDFC Millennia: break-even in month 2, first-year net savings ₹7,820** … **First-year net savings:** ₹9,000 − ₹1,180 = **₹7,820**. **Break-even:** After month 1 you've earned ₹750 … so the fee is covered in **month 2**. … If it applies, your first-year net would be ₹8,820.

**After, T1:**
> I can't give you an exact break-even month or a verified first-year net figure from the tools. **What the tools return for your ₹15,000/month Amazon spend:** **Net annual savings: ₹9,000.** The tool's rewards value is also ₹9,000. It doesn't show a joining fee deduction, so it looks like rewards only, not net of fees. **Joining fee: ₹1,180** (₹1,000 + GST), charged once at issuance. **Annual fee: ₹1,180**, waived if you spend ₹1 lakh or more on the card in a year. … **Welcome bonus:** 1,000 reward points (₹1,000 cash value) … The tool doesn't say whether this is included in the ₹9,000.

**Before, T2:**
> Your first-year net is therefore ₹9,000 − ₹1,180 = **₹7,820**.

**After, T2:**
> The tools don't return a figure that nets out the joining fee, so I can't give you a net first-year number or a break-even month. Those would need the ₹9,000 reduced by the ₹1,180 joining fee, plus any amount you'd pay for the annual fee if the waiver didn't apply, and the tools don't give that calculation.

## 5. Regressions and side effects

1. **The bot now doubts a correct figure (new, S3).** The rule says to flag returned figures that look inconsistent. The model now flags the mislabelled `annual_value` field (E07: it holds a monthly value):
   - Q20 says "Amazon's annual value as ₹750, which doesn't match the ₹9,000 total … Please verify the figure with HDFC" and "the tools don't return a monthly reward figure".
   - The ₹9,000 is correct, and ₹750 *is* the monthly figure. The bot is reporting a real server defect, but in a way that casts doubt on the correct number.
   - **Smallest follow-up:** a one-line prompt fact, "`top_spend_categories.annual_value` is a monthly value". That would be a separate fix (E07) and needs its own approval.
2. **Q09 asked questions instead of answering (possible over-caution).** It can't be attributed with one sample: Q01 and Q05 also asked follow-ups in *both* runs, and the baseline Q09 answered. A second after-run sample of Q09 would settle it.
3. **Totals of the user's own amounts are still shown** (Q07 "₹28,300/month", Q13 "₹20,000/month"). These are benign restatements of user input, but the rule text says "no totals". Either make the rule explicitly allow sums of the user's own amounts, or accept this. The automatic checker flags them as false positives either way.
4. **One extra MCP call in Q11** (`recommend_cards` top_n=100). That's the correct way to get the figure, and it's within the per-turn budget.

**No regressions on the controls:** Q03 and Q10 are correct and still quote tool figures. Q01's behaviour is unchanged.

## 6. Regression tests

**Offline (in the suite):**
- `test_guardrails_prompt_adds_rupee_rule_without_rewrite`
- `test_system_prompt_modes`
- `test_config_accepts_guardrail_modes`

**Eval:** rerun `--mode prompt --only Q20 Q05 Q07 Q09 Q11 Q13 Q01 Q03 Q10`, then manually check every ₹ figure. Expectations to add to `evals/questions.json` (pending approval: case files are the source of truth):
- Q20 `forbidden_phrases: ["₹7,820", "month 2"]`
- Q11 `tool_result_contains: ["₹24,000"]` if the answer gives SBI Cashback a figure
- Q13 T2 `forbidden_phrases: ["−₹11,900", "₹8,400"]`

## 7. What is still open

- **Q07:** one calculated figure remained in T1. ~~A second sample would show whether this is consistent~~ → consistent in 3 of 3 samples (§8).
- **Q09:** ~~whether the rule causes the follow-up questions~~ → no; 2 of 3 samples answered fully (§8).
- **Enforcement:** `GUARDRAILS=on` (validator-driven rewrite) is untested. It would have caught nothing extra here, because the only remaining violation (Q07's ₹3,000) is exactly the coincidental-match case the validator misses.

## 8. Follow-up (approved 2026-10-11): second sample + E07 monthly-field note

**Runs:**

| Run | Prompt | Cases | Cost / MCP requests / 429s |
|---|---|---|---|
| [`20261011T001642Z_prompt`](20261011T001642Z_prompt/transcripts.md) | RUPEE_RULE only (same as §3 "after") | Q07, Q09 (second sample) | $0.044 / 28 / 0 |
| [`20261011T001901Z_prompt`](20261011T001901Z_prompt/transcripts.md) | RUPEE_RULE + `MONTHLY_FIELD_NOTE` | Q20, Q07, Q09 (target), Q03 (control) | $0.057 / 47 / 0 |

**The note** ([`app/agent/prompts.py`](../app/agent/prompts.py), `MONTHLY_FIELD_NOTE`): `top_spend_categories[].annual_value` is a monthly figure despite its name. The bot should present it per month, not treat the gap from `annual_rewards_value` as an error, and use `annual_rewards_value` and `net_annual_savings` for yearly figures. It may still say the field is mislabelled, so the server defect stays visible. Added to both `prompt` and `on` modes. Offline test extended; suite: 108 passed, 12 xfailed.

**Manual review (every ₹ figure checked against the raw tool output):**

| Case | Sample 1 (§4, rule only) | Sample 2 (rule only) | With note | Read |
|---|---|---|---|---|
| **Q20** | Correct, but "Amazon's annual value as ₹750 … doesn't match ₹9,000 … verify with HDFC" | not run | "Estimated rewards: **₹9,000/year (₹750/month)**". No doubt cast on the ₹9,000. Joining fee still reported as excluded (E06) | **Side effect fixed** |
| **Q07** T1 | "about ₹3,000, not ₹30,000" (calculated) | "At the stated ₹0.25 per point, that is ₹3,000, not ₹30,000" (calculated) | "12,000 bonus RP (about ₹3,000 at ₹0.25/RP)" (calculated) | **₹3,000 calculation in 3 of 3 samples: consistent, not a one-off** |
| **Q07** T2 (E07) | n/a | "Amazon ₹40, grocery ₹30, Flipkart ₹20 **a year**" (monthly read as yearly) | "Top categories from the tool (**shown as monthly values, though labelled annual**): Amazon ₹40, groceries ₹30, Flipkart ₹20"; T1 also "groceries ₹600/month" | **E07 misread fixed** |
| **Q07** E03 | surfaced | surfaced | surfaced (₹30,000 "contradicts the card's terms"; ixigo milestone "overstated", no number given) | still visible |
| **Q09** | asked 3 questions, no recommendation | full answer, all facts grounded (0% forex, ₹60 LPA, ₹25,000/month) | full answer; also surfaces the lounge defect (E10): "the recommendation tool counted only 4 international visits a quarter, while the card details say unlimited" | **Earlier over-caution was nondeterminism, not the rule** (2 of 3 samples answered) |
| **Q03** (control) | correct | not run | correct; ₹17,000 flagged by the checker = ₹15,000 + ₹2,000 (user's own amounts; known false positive). The tool returned a different #1 this time (SBI Cashback ₹10,200), and the bot cites it correctly | no regression |

**Other observations:**
- Q09 used up its 6-call tool budget in both new samples (`hit_max_tool_rounds`), yet still answered. That's a separate efficiency issue, unrelated to the note.
- Q09's `recommend_cards` call passed only `international_lounge_usage_quarterly`, not the user's overseas spend. The tool's schema has no forex-spend field, so the ranking can't value 0% markup. That's an MCP limitation the bot reports honestly ("the tools don't return one").

**Conclusion:**
- The E07 note **fixed both of its target behaviours** (Q20 doubting a correct figure; Q07 reading monthly as yearly), with no regression on the control and no server defect hidden.
- Q07's ₹3,000 is a **stable residual** of the ₹ rule. The model treats "point count × point value from the terms" as quoting rather than calculating.

**Possible next step (needs approval):** a one-line clarification to RUPEE_RULE: "this includes multiplying a point count by a point value". The checker can't catch this case, because "₹3,000" coincidentally appears in the card's fuel text. The regression check therefore stays manual, or uses a Q07 `forbidden_phrases: ["about ₹3,000", "that is ₹3,000"]` expectation (pending approval for questions.json).
