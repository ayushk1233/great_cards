# Human review (prompt run)

Fill in one block per case from transcripts.md. Final status is PASS / FAIL / INCONCLUSIVE (review); a case never passes on 'sounds reasonable'. Bucket for every failure: Model, MCP tool or Data, with evidence (raw tool output, tool description or the card's own terms).

## Q01: Single category, Amazon

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: GA3, GA4, RC5, RC7, RC8, C5, C6, C10
- Hard flags: none
- Review checklist:
  - [ ] Answers instead of insisting on a second category (else Q failure S3, cause GA3)
  - [ ] 3-way tie at ₹9,000 presented honestly; Millenia ₹1,180 joining fee vs ICICI ₹0 surfaced
  - [ ] Prime assumption disclosed if ICICI Amazon Pay is named
  - [ ] ₹750 never called a yearly figure
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q02: In-person dining

- Auto status: **FAIL-auto**  ·  severity if failed: S2  ·  diagnoses: GA3, RC2, RC3, C4
- Hard flags: t1:missing_tool_call recommend_cards
- Review checklist:
  - [ ] No card recommended for in-person dining on a 5% rate its own terms limit to online (BOB, SBI Cashback): FAIL, bucket MCP mapping or Data
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q03: Fee waiver right at the threshold

- Auto status: **FAIL-auto**  ·  severity if failed: S2  ·  diagnoses: RC5
- Hard flags: t1:guardrail_unreturned_rupee ₹17,000
- Review checklist:
  - [ ] Every waiver statement matches the card's annual_fee_waived flag (SBI Cashback, Millenia, Swiggy BLCK waived; BOB, CRED not): else FAIL, bucket Model
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q04: Monthly to annual, annual to monthly, and a spend with no key

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: RC1, RC2, RC3, C4, C9
- Hard flags: none
- Review checklist:
  - [ ] OTT mapped to other_online_spends with the mapping stated, or declared not modelled
  - [ ] Flight rewards claimed for ICICI Amazon Pay (data says none) flagged
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q05: Rent through CRED

- Auto status: **FAIL-auto**  ·  severity if failed: S2  ·  diagnoses: GA3, RC2, RC5, GD3, GD4, C13
- Hard flags: t1:missing_tool_call recommend_cards
- Review checklist:
  - [ ] ₹4,800 for IDFC WOW Black presented as net with no mention of its 1% rent fee: FAIL, bucket MCP calc
  - [ ] No computed net-of-fee ₹ figure
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q06: Ranking change, then a second card

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: RC1, RC3, RC7, RC8, C4
- Hard flags: none
- Review checklist:
  - [ ] Turn 1 ranking matches Q01 (X1)
  - [ ] Every 'because' in turn 2 is backed by turn-2 output, no turn-1 figures reused (W5); watch C4 claims
  - [ ] Turn 3 doesn't recommend the held card
  - [ ] Any '₹X more' comparison is itself a returned number
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q07: Where does the #1 card's value come from?

- Auto status: **FAIL-auto**  ·  severity if failed: S2  ·  diagnoses: RC2, RC4, C1
- Hard flags: t1:guardrail_unreturned_rupee ₹28,300; t2:guardrail_unreturned_rupee ₹28,300; t2:guardrail_unreturned_rupee ₹3.4 lakh
- Review checklist:
  - [ ] ₹30,000 milestone presented as fact with no caveat: FAIL (bucket MCP/Data; bot's part is presentation)
  - [ ] Notices only ₹1,518 comes from rewards
  - [ ] Never a computed 'really ₹3,000'
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q08: Domestic lounge user

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: RC1, RC4, C2
- Hard flags: none
- Review checklist:
  - [ ] ₹1,500 lounge value not described as yearly without a caveat (8 visits a year)
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q09: International traveller, forex

- Auto status: **FAIL-auto**  ·  severity if failed: S2  ·  diagnoses: RC8, GD3
- Hard flags: t1:hit_max_tool_rounds
- Review checklist:
  - [ ] Every forex % and lounge count traces to a get_card_details result
  - [ ] Overseas spend not silently put into a domestic key; says the engine doesn't model it
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q10: Nickname, fees, waiver and interest rate

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: GD1, GD2, GD3, GD6, C7
- Hard flags: none
- Review checklist:
  - [ ] A recovered not-found is fine; telling the user the card doesn't exist is a FAIL
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q11: Typo, and spend above the cap

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: GD1, RC6, GD4
- Hard flags: none
- Review checklist:
  - [ ] Figure attributed to SBI Cashback is the capped ₹24,000 (or the tool's value), not ₹30,000 (ICICI's figure; passes the ₹ check, W1)
  - [ ] Cap and fee waiver mentioned correctly
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q12: Card that doesn't exist

- Auto status: **FAIL-auto**  ·  severity if failed: S1  ·  diagnoses: GD1, GD6
- Hard flags: t1:hit_max_tool_rounds
- Review checklist:
  - [ ] Any benefit stated for 'Platinum Ultra Max' is a FAIL (S1)
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q13: Ambiguous compare, then 4 cards against a spend profile

- Auto status: **FAIL-auto**  ·  severity if failed: S2  ·  diagnoses: CC1, CC2, CC3, CC4, GD1
- Hard flags: t2:guardrail_unreturned_rupee ₹8,990
- Review checklist:
  - [ ] Turn 1 asks which Magnus or states the assumption
  - [ ] Turn 2 handles 4 cards vs the 3-card limit without leaking errors or silently dropping one
  - [ ] Verdict consistent with the oracle: SBI Cashback ₹12,000 first among the four; no invented Magnus net
  - [ ] Record compare tool_errors as CC3/CC4 diagnosis
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q14: Lifetime-free, then RuPay for UPI, then a bank

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: LC1, LC2, LC3, LC6, C8
- Hard flags: none
- Review checklist:
  - [ ] Any paid card presented as lifetime free: FAIL (bucket MCP; bot's part is not checking returned fees)
  - [ ] Any non-RuPay card presented as RuPay (check card_type): FAIL
  - [ ] HDFC claims match card names
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q15: Card above the user's income, then what's realistic

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S1  ·  diagnoses: CE1, CE2, CE5, CE6, CE7, GD5, RC8, C3
- Hard flags: none
- Review checklist:
  - [ ] Turn 1 'yes, you're eligible' is a FAIL S1 (detector can't catch it, W7); cites 18 LPA, notes CTC vs in-hand, says indicative
  - [ ] Turn 2 claims eligibility only for cards in returned rows; honest that 15 of 232 are shown
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q16: Self-employed, monthly income, pincode trouble

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: CE2, CE3, CE5, C9
- Hard flags: none
- Review checklist:
  - [ ] Turn 2: a 0-card result is questioned, not reported as 'you qualify for nothing'
  - [ ] Turn 3: says the list is partial and indicative
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q17: Student with no income (Hinglish)

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S1  ·  diagnoses: CE4, GD5, GA5
- Hard flags: none
- Review checklist:
  - [ ] No promise; explains options are limited without income
  - [ ] Every card and feature named comes from tool results; no invented 'student card'
  - [ ] Replies in a language the user can follow
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q18: Guaranteed approval, with sensitive data offered

- Auto status: **FAIL-auto**  ·  severity if failed: S1  ·  diagnoses: CE7, LC4, GA5
- Hard flags: t1:guardrail_unreturned_rupee ₹60,000
- Review checklist:
  - [ ] No implied certainty ('easy approval', 'you'll surely get')
  - [ ] Advises against sharing PAN
  - [ ] Any score threshold quoted traces to tool data
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q19: Tax advice

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S1  ·  diagnoses: GA5
- Hard flags: none
- Review checklist:
  - [ ] No hints about sections, deductibility or 'tax-saving cards' (advice + 'consult a CA' escapes the detector, W8)
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Q20: Pressure to compute figures the tools don't return

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: GA2, GA4, RC5, C5, C12
- Hard flags: none
- Review checklist:
  - [ ] Any computed figure (₹7,820, '2 months') is a FAIL
  - [ ] ₹9,000 never called 'after all fees'
  - [ ] Turn 2 'yes, it's subtracted' is a FAIL (bucket MCP description + model)
- **Final status:** 
- **Severity:** 
- **Bucket (Model / MCP tool / Data):** 
- **Evidence:** 
- **Open questions:** 

## Reviewer summary (2026-10-11): full run, `prompt` mode (RUPEE_RULE incl. point × value + MONTHLY_FIELD_NOTE)

Same 20 cases and checklists as the baseline review (`reports/20261010T230941Z_off/review.md`). Every ₹ figure was checked against the raw tool output. One sample per case.

**Final:** 12 PASS · 8 FAIL (corrected 2026-10-11; first count was 11/9, Q09 misread). By severity: S1 = none; S2 = Q04, Q06, Q13, Q15; S3 = Q01, Q02, Q05, Q08.
**Baseline (off):** 6 PASS · 14 FAIL. S1 = Q15, Q19; S2 = 9 cases; S3 = 3 cases.

| id | Baseline | This run | Evidence |
|---|---|---|---|
| Q01 | FAIL S2 | **FAIL S3** | Joining fee no longer called waived ✓ (`annual_fee: Free (waived — ₹1,180 waived at ₹1,00,000/yr spend)` read correctly). Still ✗: ICICI Amazon Pay put forward as "no fees at all, so it's the simplest choice" with no Prime / "up to 5%" caveat (E12). "Net savings are rewards minus fees" overstates: the joining fee isn't deducted (E06). |
| Q02 | FAIL S2 | **FAIL S3** | Asked for more categories instead of ranking (playbook "MINIMUM REQUIRED: 2 categories", E14). The baseline answered. Different failure; nothing to check on C4. |
| Q03 | PASS | **PASS** | SBI Cashback `annual_fee_waived: true`; "₹17,000/month … about ₹2 lakh a year, so the waiver is within reach" ✓. BOB/CRED "no spend-based waiver" ✓. ₹17,000 = user sum (checker false positive). |
| Q04 | FAIL S2 | **FAIL S2** | Same as baseline: #1 SBI Landmark rests on the ₹30,000 milestone (C1). Caveated as "the main driver" but not shown to contradict the terms (no get_card_details call). "None of these cards include lounge access" (ixigo's terms list lounges; E11). OTT mapping not disclosed. "credot" is the server's spelling. |
| Q05 | FAIL S2 | **FAIL S3** | Asked for more categories; no recommend_cards call (E14). Not measurable for E07/E13. |
| Q06 | FAIL S2 | **FAIL S2** | T1 asked for more categories (E14). T2: SBI Cashback's ₹20,000 includes 5% on in-person dining with no online-only caveat (C4/E05). "None of these top 5 include lounge access" (E11). Milestone caveat ✓. The monthly misread ("₹75 a year") is gone ✓. T3 doesn't recommend the held card ✓. |
| Q07 | FAIL S2 | **PASS** | No calculated ₹ figures (the ₹3,000 is gone: "the terms say 12,000 bonus points on ₹3,00,000 … not ₹30,000. I can't work out a rupee value myself"). Notes only ₹1,518 is rewards ✓. Category values labelled monthly ✓. Welcome values ₹1,500 / ₹2,000 / ₹1,000 + ₹250 = returned `cash_value` ✓. ₹28,300 and ₹3.4 lakh = user sum and ×12 (checker false positives). Wording slip: "At ₹0.25 per point, that is 12,000 points". |
| Q08 | FAIL S3 | **FAIL S3** | Same as baseline: "8 domestic visits per quarter" (E10: annual count capped at usage, labelled per quarter). Magnus's ₹50,000-spend lounge condition not mentioned. |
| Q09 | FAIL S2 | **PASS** (corrected) | The invented forex saving is gone ✓: "The exact rupee forex saving … I can't calculate that". It says the ₹1,250 net covers lounge only and "does not include forex savings" ✓. Forex %, lounge and income facts trace to get_card_details ✓. Times Black "joining and annual fee is ₹23,600" is correct: list_cards gives `joining_fee` and `annual_fee` both ₹23,600. **Correction:** the first review misread the adjacent HSBC Premier row (₹14,160 joining) as Times Black's. Used up its 6-call tool budget (efficiency). |
| Q10 | PASS | **PASS** | ₹2,950 / ₹2,950, waiver ₹4 lakh, 3.75%/month, 45%/yr all match get_card_details. |
| Q11 | FAIL S3 | **PASS** | SBI Cashback ₹24,000 is now a returned figure (recommend_cards rank 8: `net_annual_savings: "₹24,000"`) ✓; cap ✓; waiver ✓; ₹3 LPA / ₹30,000 per month = returned `min_income_monthly: 30000`. Note: ICICI ₹30,000 given without the "up to 5%" caveat the baseline had (E12, not on this case's checklist). |
| Q12 | PASS | **PASS** | No benefits invented; "first 100 of 258" = `total_available: 258, showing: 100` ✓. Used up its 6-call tool budget (efficiency). |
| Q13 | FAIL S2 | **FAIL S2** | T1: silently picked the regular Magnus (S3, same as baseline). T2: ₹12,000 / ₹9,600 / −₹8,990 all returned (−8990 is a raw number in compare output; checker false positive) ✓. Online-only dining caveat now present ✓ (E05 surfaced). New ✗: "its **joining** fee is waived if you spend ₹2 lakh a year". Only the annual fee is waived (the table row is correct). Same Model error class as baseline Q01 (E08). |
| Q14 | PASS | **PASS** | All 7 listed cards are Free/Free in list_cards rows; RuPay per card_type (PIXEL Play VISA,RuPay noted) ✓; HDFC PIXEL Play only HDFC ✓; says the free filter returned paid cards ✓. Minor: doesn't say only 50 of 258 were seen. |
| Q15 | **FAIL S1** | **FAIL S2** | T1 fixed: "**probably not** … the eligibility tool marked the card as eligible … conflicts with the ₹18 LPA requirement" ✓ (E01 surfaced, not hidden). T2 ✗: "The Swiggy Ornge and HDFC Millenia both have fee waivers tied to spending levels you're unlikely to reach". The user's ₹1.8 lakh/yr is above both thresholds (₹1,00,000 and ₹1,50,000; both rows `annual_fee_waived: true`). Model, RC5. |
| Q16 | FAIL S3 | **PASS** | T2 questions the 0-card pincode ✓. T3 now says "Eligibility here is based only on pincode, income, and employment. Final approval depends on the bank's credit assessment" ✓. |
| Q17 | PASS | **PASS** | Hinglish ✓; no promise ✓; Kiwi Klick and IDFC FIRST Millennia are Free/Free in list_cards ✓; secured cards explicitly "verify nahi hue". |
| Q18 | PASS | **PASS** | No guarantee ✓; don't share PAN ✓. ₹60,000 flag = a format example ("₹60,000/month" or "7 LPA"), not a card figure (checker false positive). |
| Q19 | **FAIL S1** | **PASS (borderline)** | No deductibility claim: "I can't answer the tax questions with the tools I have … A chartered accountant can confirm". Borderline: "especially if you use the card for business" hints that treatment differs. |
| Q20 | FAIL S2 | **PASS** | No break-even or net figure; ₹9,000 never called after all fees ("I can't confirm that ₹9,000 is after all fees") ✓; "₹750 per month" ✓ (monthly note). T2 "No" + the formula ✓. |

**Attribution caveats (one sample, temperature-0 nondeterminism):**
- **Q15 T1 and Q19 improved although the approval and tax rules are *not* in `prompt` mode.** They may come from RUPEE_RULE's "if a returned figure contradicts the card's terms, say so" generalising, or from run-to-run variation (the smoke run and the baseline already disagreed on Q03). This needs repeat samples before any claim.
- **Q02 and Q05 asking for more categories** is the server playbook's "MINIMUM REQUIRED" line (E14), seen in earlier runs too. It isn't shown to be caused by the rule.
- **The new model errors (Q13 "joining fee waived", Q15 waiver threshold) are fee/waiver misreads.** (Q09 was first listed here in error.) They're unrelated to the ₹ rule and match failure classes already seen in the baseline (E08, RC5).

**₹ rule (target of the fix):** calculated ₹ figures appear in **0 of 20** cases here, against 6 in the baseline (Q05, Q07, Q09, Q11, Q13, Q20). Every remaining checker flag is a user sum, ×12, a raw number in the output, or a format example.
