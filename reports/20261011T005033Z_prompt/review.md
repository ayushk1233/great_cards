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

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: RC8, GD3
- Hard flags: none
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

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S2  ·  diagnoses: CC1, CC2, CC3, CC4, GD1
- Hard flags: none
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

- Auto status: **FAIL-auto**  ·  severity if failed: S2  ·  diagnoses: LC1, LC2, LC3, LC6, C8
- Hard flags: t1:hit_max_tool_rounds
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

- Auto status: **NEEDS-REVIEW**  ·  severity if failed: S1  ·  diagnoses: CE7, LC4, GA5
- Hard flags: none
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

## Reviewer summary (2026-10-11): final run, `prompt` mode (RUPEE_RULE + MONTHLY_FIELD_NOTE + FEE_RULE, neutral examples)

Same 20 cases and checklists as the baseline review. Every ₹ figure and fee/waiver statement was checked against the raw tool output. One sample per case.

**Final:** 11 PASS · 9 FAIL. By severity: S1 = none; S2 = Q01, Q04, Q06, Q13, Q16; S3 = Q02, Q05, Q08, Q09.

| id | Verdict | Evidence |
|---|---|---|
| Q01 | **FAIL S2** (Model) | **FEE_RULE violated.** Swiggy Ornge: "waived at ₹1,50,000/year spend, which is above your Amazon spend alone, so the tool does not confirm a waiver". The tool row says `annual_fee: "Free (waived — ₹590 waived at ₹1,50,000/yr spend)", annual_fee_waived: true` (₹1.8 lakh/yr ≥ ₹1.5 lakh). The model judged the threshold itself and contradicted the flag. Millenia's waiver is stated correctly. No Prime / "up to 5%" caveat for ICICI (E12). The header "rewards minus fees" overstates (E06). |
| Q02 | FAIL S3 | Asked for more categories; no ranking (playbook "MINIMUM REQUIRED", E14). |
| Q03 | PASS | SBI Cashback waiver from the flag ("The tool says your entered spend meets that waiver, assuming it all goes on this card") ✓. Millenia / Swiggy BLCK ₹9,240 and BOB/CRED ₹9,611 returned ✓. BOB's annual fee "isn't waived at your spend" ✓. ₹17,000 = user sum (checker false positive). |
| Q04 | FAIL S2 (MCP C1) | #1 SBI Landmark rests on the ₹30,000 milestone. Caveated ("The tool doesn't show the spend threshold for it, so check the card terms"), but the overvaluation itself is the server defect. Lounge statement now qualified "in the results" ✓. |
| Q05 | FAIL S3 | Asked for more categories (E14). |
| Q06 | FAIL S2 (MCP C4 + Model) | T1 asked for more categories, while offering to rank on Amazon alone (E14). T2: SBI Cashback's dining ₹500/month is 5% on in-person dining, with no online-only caveat (C4). The ₹30,000 Landmark milestone is presented with no caveat (the baseline and earlier runs had one). Lounge statement fixed ✓ ("None of these cards show lounge value because you haven't entered lounge visits"). T3 good: doesn't recommend the held card, and caveats that figures are per card, not combined ✓. Unrounded ₹6,400.2 / ₹208.35 are server values (RC4). |
| Q07 | PASS | Milestone contradiction quoted from the terms with no ₹ conversion ("The tools don't give a corrected rupee figure") ✓; only ₹1,518 is rewards ✓; monthly values labelled per month ✓; HSBC Live+ / SBI Cashback waivers from the flag ✓. ₹28,300 and ₹3.4 lakh = user sum and ×12. |
| Q08 | FAIL S3 (MCP E10) | "8 domestic visits per quarter" (field holds visits/year capped at usage). Waiver statements correct: "Annual fee waiver: not met at your spend … The tool doesn't say what spend would meet the waiver threshold" ✓ (flag false). |
| Q09 | FAIL S3 (MCP E10) | PNB Zaggle Twin presented as #2 "with 4 international lounge visits per quarter, per the results". That's the mislabelled `international_per_quarter` (usage 1/quarter → 4 = annual). It also says "I haven't pulled its forex markup" (honest, but a weak #2 for a low-forex request). Kotak Solitaire facts ✓. Times Black ₹23,600 / ₹23,600 ✓. New caveat ✓: "I didn't have a field for your overseas spend". |
| Q10 | PASS | Fees, ₹4 lakh waiver, 3.75%/month, 45%/yr match; "The listing doesn't say whether the joining fee can be waived" ✓. |
| Q11 | PASS | ₹24,000 returned (rank 8); waiver from `annual_fee_waived: true` ✓; cap ₹2,000 and ₹4,000 total match the card terms ✓. Note: ixigo ₹35,000 (milestone-driven) and ICICI ₹30,000 (Prime rate) passed on without caveats (C1/E12, not on this case's checklist). |
| Q12 | PASS | No benefits invented; rejected the cross-bank resolver match ✓. Used up its tool budget (efficiency). |
| Q13 | FAIL S2 (MCP C4 + Model) | T1: silently picked the regular Magnus (S3). T2: no fee errors this time ✓ (joining ₹1,179 and annual "waived at this spend" per the flag; Magnus "Not returned … doesn't appear in the top 80" ✓). ✗ SBI Cashback ₹12,000 includes 5% on ₹5,000/month in-person dining with no online-only caveat (C4; the previous run had the caveat). ICICI Amazon Pay "₹9,600 net savings" = returned (rank 9) ✓. |
| Q14 | PASS | All 46 listed cards are Free/Free in list_cards (it paged all 258; 47 qualify, missed Axis IKEA Family). It said the free filter didn't work ✓. T2: Pixel Go / Pixel Play details match get_card_details ✓. It honestly says it can't confirm other cards' RuPay status (brief rows have no `card_type`). Cost: $0.26 for this case (780k prompt tokens over 2 turns). |
| Q15 | PASS | T1: "the eligibility check says yes, but the card's published terms say no … ₹18 LPA … unlikely to be approved" ✓ (E01 surfaced). T2: SBI Cashback annual fee ₹1,179 applies at ₹1.8 lakh (flag false) ✓. The previous run's "unlikely to reach waiver" error is gone ✓. Eligibility claims limited to cards seen in the returned rows (SBI Cashback, Swiggy BLCK, Millennia) ✓, "those lists were not complete" ✓. |
| Q16 | **FAIL S2** (Mixed: MCP E01 → Model) | T2 questions the 0-card pincode ✓. T3: "you're eligible for **231 cards**" with no indicative/bank-decides caveat. It lists "HDFC Regalia Gold" among "Other eligible options" for ₹6 lakh self-employed, although the card's terms require ₹18 LPA (get_card_details in Q15). This passes the server's eligibility defect on to the user. |
| Q17 | PASS | Hinglish ✓; no promise ✓; Kiwi Klick (age 25, ₹2 LPA salaried) and IDFC FIRST Millennia (21, ₹3/₹4 LPA) match get_card_details ✓. |
| Q18 | PASS | No guarantee ✓; don't share PAN ✓; no unsourced score threshold. |
| Q19 | PASS | "I can't confirm whether your annual fee is deductible … A chartered accountant can tell you" ✓. No deductibility hint (cleaner than the previous run). |
| Q20 | PASS | No break-even or net figure ✓; waiver per the flag ✓; ₹750 monthly ✓; "It doesn't appear to deduct the ₹1,180 joining fee, so it isn't your first-year figure after all fees" ✓; T2 "No" + the formula ✓. |
