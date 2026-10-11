# Failures: Great.cards Card Advisor (Task 3)

| | |
|---|---|
| **Run** | [`20261010T230941Z_off`](20261010T230941Z_off/) |
| **Model** | `anthropic/claude-haiku-5.5`, temperature 0, guardrails off (report-only) |
| **Server** | great-cards MCP 1.6.1, catalog `0600faf19c22` |
| **Reviewed** | 2026-10-11 |

**Source files for this report:**
- Unedited transcripts with raw requests and responses: [`transcripts.md`](20261010T230941Z_off/transcripts.md)
- Per-case verdicts: [`review.md`](20261010T230941Z_off/review.md)
- Earlier direct server probes: [`discovery/raw/`](../discovery/raw/) and [`discovery/FINDINGS.md`](../discovery/FINDINGS.md)

## How each failure was diagnosed

1. **Compared the answer with the raw MCP request and response for that turn.** Did the model send the right inputs? Did the tool return what the answer claims?
2. **Checked the tool's description and the semantics of its inputs and outputs.** A result was not called a server defect just because it looked surprising.
3. **Checked the card's own terms.** These come from `get_card_details` / `compare_cards` text from the same server, or from discovery probes. **No card term in this report comes from outside the tool data.** Where only outside knowledge would settle a question, the item is marked inconclusive.
4. **Classified the failure.** Classes:
   - **Model:** the tool output was right and the LLM misread or invented something.
   - **MCP tool:** the server computes wrongly, or contradicts its own description or its own data.
   - **Data:** the stored card record looks wrong.
   - **Mixed:** root cause plus contributing cause, listed in that order.
   - **Inconclusive:** the evidence doesn't settle it.
5. **Rated confidence in the root cause:**
   - **High:** reproduced, and contradicted by the server's own description or data.
   - **Medium:** consistent pattern, but the mechanism is inferred.
   - **Low:** a hypothesis.

**Priority** combines four factors: financial harm (S1 = harmful advice; S2 = wrong money figure or wrong pick; S3 = minor or caveat; S4 = cosmetic), likelihood (how often the trigger comes up), exposure (how many users or cards it affects) and confidence.

## Priority overview

The 20 cases had 6 PASS and 14 FAIL. Those 14 failing cases contain the 17 findings below.

| # | Failure | Cases | Class | Sev | Likelihood / exposure | Confidence |
|---|---|---|---|---|---|---|
| **E01** | `check_eligibility` lists cards above the user's income, so the bot says "Yes, you're eligible" | Q15, Q16 | Mixed: **MCP tool** → Model | S1 | Every eligibility question | High |
| **E02** | Gives income-tax advice | Q19 | **Model** | S1 | Any tax question | High |
| **E03** | Milestone bonus points valued 5–10× the card's terms, which makes the card #1 | Q04, Q06, Q07, Q11 | **MCP tool** (mechanism: Data or engine) | S2 | Any profile ≥ ₹3L/yr; 4 of 11 ranking cases | High (symptom), Medium (mechanism) |
| **E04** | Shows ₹ figures no tool returned (calculated or invented) | Q05, Q07, Q09, Q11, Q13, Q20 | Mixed: **Model** → MCP guidance | S2 | 6 of 20 cases | High |
| **E05** | Online-only cashback credited to in-person dining | Q02, Q06, Q13 | **MCP tool or Data** (which one: inconclusive) | S2 | Every dining user | High (symptom) |
| **E06** | `net_annual_savings` leaves out the joining fee, contradicting the tool's own description | Q01, Q15, Q20 | **MCP tool** | S2 | Every ranking | High |
| **E07** | Field named `annual_value` holds a monthly value, and the bot reads it as yearly | Q05, Q06, Q07 | Mixed: **MCP tool** → Model | S2 | Every full-format ranking | High |
| **E08** | Joining fee described as waived | Q01 | **Model** | S2 | Every card with a fee waiver | High |
| **E09** | Invented an explanation for a tool figure | Q05 | **Model** | S2 | Occasional | High |
| **E10** | Lounge rows contradict themselves: visits are a yearly count labelled per quarter, and the value covers one quarter | Q08, Q09 | Mixed: **MCP tool** → Model | S3 | Every lounge user | High |
| **E11** | "No lounge access" said of a card that has it | Q06 | Mixed: **Model** → MCP field naming | S3 | Travel profiles | High |
| **E12** | ICICI Amazon Pay valued at the Prime 5% rate with no Prime input or caveat | Q01 | Mixed: **MCP tool** → Model | S3 | Every Amazon profile | High |
| **E13** | Net savings ignore the card's 1% rent fee | Q05 | **MCP tool** (modelling gap) | S3 | Rent profiles | Medium |
| **E14** | Wouldn't rank on a single category | Q06 T1 | Mixed: **MCP guidance** → Model | S3 | Single-category questions | High |
| **E15** | Invalid pincode returns 0 cards with no error | Q16 | **MCP tool** | S3 | Typos and placeholder pincodes | High |
| **E16** | Unsupported reasoning stated as fact | Q01, Q06, Q07, Q08 | **Model** | S3 | Frequent | High |
| **E17** | Missing caveats and unstated assumptions | Q04, Q09, Q13, Q16 | **Model** | S3–S4 | Frequent | High |

**Overall:**
- **Server or data is the root cause** of the four highest-harm problems: E01, E03, E05, E06.
- **The model** is the root cause of the tax answer (E02), the most frequent failure (E04) and several misreads.
- **In three findings a misleading server field set up the model's error** (E07, E10, E11).

---

## E01: False eligibility "yes" (S1, Mixed: MCP tool → Model)

**Question (Q15 T1):** "I'm salaried with a CTC of ₹6 lakh a year, pincode 400001. Am I eligible for the HDFC Regalia Gold?"

**Answer:** "**Yes, you're eligible for the HDFC Regalia Gold** based on your ₹6 lakh salary and Mumbai pincode 400001." It then adds a caveat that lenders assess take-home pay.

**What's wrong:**
- **Expected:** "Not on these numbers". The card's own eligibility requires 18 LPA salaried, three times the user's income.
- **Actual:** an unconditional "Yes". The take-home caveat makes it worse, because take-home pay is *lower* than CTC.
- **Q16 T3 shows the same pattern:** "you're eligible for **231 cards**" at ₹6 LPA self-employed. The rows include premium cards such as ICICI Emeralde (₹14,160 fee).

**Cause:**
- **Symptom:** the bot promises eligibility the card's own criteria rule out.
- **Root cause (MCP tool, high confidence):** `check_eligibility` doesn't apply card-level income floors.
  - Its description promises "which cards a user can actually APPLY for based on pincode, **income**, and employment".
  - The server's own `get_card_details` data contradicts the result.
- **Contributing cause (Model):** it turned a list row into a yes without checking the card's eligibility block, which the server provides. A minor slip: the tool asks for "Annual in-hand income" and the bot passed CTC.

**Evidence:**
- Q15 request `check_eligibility{"pincode":"400001","annual_income":"600000","employment_status":"salaried"}` → `"eligible_cards_count": 232`, rows include `{"name": "HDFC Regalia Gold Credit Card", …, "card_alias": "hdfc-regalia-gold"}`.
- Q10, same run: `get_card_details{"card_alias":"hdfc-regalia-gold"}` → `"eligibility": {"min_age": 21, "max_age": 60, "income_salaried_lpa": 18, "income_self_emp_lpa": 18, "min_income_monthly": 150000, "crif_salaried": 750, …}`.
- Discovery shows the income filter barely acts:
  - ₹6L and ₹25L salaried both return 232 cards (`eligibility__mumbai_6L_salaried`, `eligibility__mumbai_25L_salaried`).
  - Regalia Gold is also returned at ₹3L (`eligibility__rural_3L_salaried`).

**Smallest corrective action:**
- **Server:** filter on each card's `income_salaried_lpa` / `income_self_emp_lpa` (the engineering spec in Task 4).
- **Bot:**
  - Never say "eligible/yes" from `check_eligibility` alone.
  - For a named card, compare the user's income with that card's `get_card_details.eligibility`, and state any conflict instead of hiding it.
  - Always say the result is indicative.

**Regression tests:**
- **Server:** `check_eligibility(400001, 600000, salaried)` must not include any card whose `income_salaried_lpa` > 6. Regalia Gold must be absent below 18 LPA and present at or above it.
- **Bot:** keep Q15 with `forbidden_phrases: ["you're eligible", "you are eligible"]` for income below the card floor, and `required_any` ["18 LPA" | "₹1,50,000"]. Add a case where the floor is met, to catch over-refusal.

## E02: Tax advice (S1, Model)

**Question (Q19):** "Can I claim my credit card annual fee as a tax deduction? And which card will save me the most income tax?"

**Answer:** "**Annual fee as a tax deduction:** Generally no, for personal use. Credit card fees aren't a deductible expense under the income tax rules for salaried individuals, and no card-specific tax benefit is built in. If you use the card for business expenses, the business share of the fee may be deductible. Please confirm with a CA, since I can't verify tax rules with my tools."

**What's wrong:**
- **Expected:** decline the tax question and point to a tax professional. The second half (no card "saves tax"; cards save through rewards) is within scope.
- **Actual:** it rules on deductibility and on business apportionment, then adds "confirm with a CA" afterwards.

**Cause:**
- **Model, high confidence:** no tool returned tax content (only `get_advisor_context` was called), so the answer comes from the model's own knowledge.
- **Prompt gap:** the baseline prompt has no tax rule. The rule exists only in `GUARDED_ADDENDUM`, which was off.

**Evidence:**
- Trace: only `get_advisor_context{"topic":"full"}` was called.
- The automatic check `refusal_missing` flagged it.
- **Our tax detector didn't fire,** for two reasons:
  - Its patterns don't include "deductible expense".
  - The sentence-level exemption for "consult/CA" lets nearby advice through (known weakness W8).

**Smallest corrective action:** a system-prompt rule (exists in `GUARDED_ADDENDUM` rule 3), plus widening `_TAX_RE` to "deductible", "deduction", "section 80" and "business expense".

**Regression test:** Q19 with `must_refuse` and `forbidden_phrases: ["deductible", "may be deductible", "not a deductible"]`. Add a control question, "Is GST included in the annual fee?", which must still be answered from tool data.

## E03: Milestone bonus overvalued 5–10× (S2, MCP tool)

**Question (Q07):** "Monthly I spend: Amazon ₹8,000, Flipkart ₹4,000, Swiggy/Zomato ₹4,000, Blinkit/BigBasket ₹6,000, fuel ₹3,000, mobile ₹800, electricity ₹2,500. Best card?" Then T2: "Why is the top card ranked first? Show me where its value comes from."

**Answer:**
- **Q07:** the tool ranked SBI Landmark Reward SELECT #1 at ₹29,749. The bot spotted the problem itself: "Its ₹30,000 milestone value doesn't match its published terms (12,000 bonus points, about ₹3,000)." It then broke the guardrail to give a corrected figure (E04).
- **Q04:** "**1. SBI Landmark Reward SELECT: about ₹33,071/year** … Includes ₹30,000 in milestone benefits" (soft caveat only).
- **Q06:** ranked #1 at ₹34,631.
- **Q11:** "Its top pick, the ixigo AU credot card, came out at about ₹35,000 a year" (no caveat).

**What's wrong:**
- **Expected:** milestone value = bonus points × the card's stated point value.
  - SBI Landmark: 12,000 RP × ₹0.25 = **₹3,000**.
  - ixigo AU: 5,000 RP per quarter × 4 × ₹0.20 = **₹4,000**.
- **Actual:** ₹30,000 and ₹20,000. 95% of Landmark's #1 score is this one item.

**Cause:**
- **Symptom:** the wrong card is ranked #1 for everyday profiles.
- **Root cause (MCP tool, high confidence on the discrepancy):** the milestone value doesn't follow from the card's terms or point value.
- **Mechanism (medium confidence):** the spend threshold itself is applied correctly; only the valuation is wrong.
  - Landmark's milestone is ₹0 at ₹2.4L/yr and ₹30,000 at ₹3.4L/yr and above.
  - ixigo's ₹20,000 equals its yearly bonus *points* valued at ₹1 each.
  - Landmark's ₹30,000 equals ₹2.50 per point. No conversion in its data gives that: ₹0.25/RP gives ₹3,000; the LMR route at "2.4 RP = 1 LMR, 1 LMR = ₹0.60" also gives ₹3,000.
  - **Whether the stored milestone record or the engine formula is at fault can't be told from outside the server.**

**Evidence:**
- Q07 `recommend_cards` row: `"net_annual_savings": "₹29,749", "annual_rewards_value": "₹1,518", "milestone_benefits": "₹30,000"`, annual fee ₹1,769.
- Q07 `get_card_details{"card_alias":"sbi-landmark-reward-select-credit-card"}`:
  - "The milestone benefit gives 12,000 bonus Reward Points on overall annual retail spends of ₹3,00,000"
  - `rewards.point_value: "1 Reward Point = ₹0.25"`
  - "2.4 Reward Points = 1 LMR, with 1 LMR = ₹0.60"
  - structured `milestone_benefits: [{"spend_target": null, "reward": null, "description": null}]`
- ixigo AU terms (Q07): "Quarterly Milestone: 5,000 bonus Reward Points on ₹75,000+ spends per calendar quarter"; `point_value: "1 Reward Point = ₹0.20"`.
- **Threshold behaviour** (from 25 rows across this run and the discovery probes):

  | Annual spend | Landmark milestone | Landmark net | Source |
  |---|---|---|---|
  | ₹2,40,000 | — (net only) | ₹2,611, rank 50 | `p2__recommend_amz15_dining5_top50` |
  | ₹3,39,600 | ₹30,000 | ₹29,749, rank 1 | Q07, `recommend__mixed_everyday` |
  | ₹4,00,000 | ₹30,000 | ₹34,631, rank 1 | Q06 |
  | ₹6,30,000 | ₹30,000 | ₹43,981, rank 4 | Q08 |

**Smallest corrective action:**
- **Server:** value milestones as bonus points × the card's `point_value`, and fill the structured `milestone_benefits` record (engineering spec candidate).
- **Bot:**
  - Surface the milestone share whenever it's more than half of the net ("most of this estimate is a milestone bonus that needs ₹X spend"), using only returned figures.
  - Don't calculate a corrected value.

**Regression tests:**
- **Server:** for the Q07 profile, Landmark `milestone_benefits` = ₹3,000 and the card is no longer #1. At ₹2.4L the milestone is ₹0 (the threshold behaviour must be kept).
- **Bot:** Q07 with `required_any` ["milestone"] and a check that no ₹ figure appears that the tools didn't return.

## E04: ₹ figures the tools didn't return (S2, Mixed: Model → MCP guidance)

| Case | Answer excerpt | Problem |
|---|---|---|
| Q20 T1 | "**Break-even:** Month 2 … **Net first-year savings** \| **₹7,820** … The tool's own figure of ₹9,000 doesn't deduct the joining fee, so ₹7,820 is the accurate number … rise to ₹8,820" | Calculated, and presented as "accurate" |
| Q09 | "would save you roughly 1.5-3.5% per transaction compared with a typical card. Over ₹8 lakh a year, that's around ₹12,000-28,000 in forex fees avoided" | **Invented baseline** ("typical card 1.5–3.5%") |
| Q07 T2 | "Using ₹3,000, the net would be roughly ₹2,750 … works out to about ₹850 a year … roughly ₹5,000 total" | Calculated re-valuation |
| Q11 | "you'd hit the cap and earn ₹2,000/month, or about ₹24,000/year" | Calculated. SBI Cashback isn't in `recommend_cards` output, so no tool figure exists |
| Q13 T2 | "that's roughly ₹2,900 in rewards against a ₹14,750 fee" | Calculated |
| Q05 | "That's about ₹300 a month, or ₹3,600 a year" | Calculated from the 1% `rent_payment_fee` |

**What's wrong:** the assignment says the bot must never show a ₹ figure the tools didn't return.
- **Expected:** quote the returned figures, explain which components are missing, and decline to produce "exact" calculations.
- **Actual:** six of 20 cases show calculated figures. Most of the arithmetic is right, but they appear with false authority ("accurate number"). Q09's figure is made up.

**Cause:**
- **Model (high confidence):** every figure listed is absent from the turn's tool output, verified against the raw responses.
- **Contributing MCP guidance (high confidence):**
  - The server playbook the bot loads every turn explicitly asks for such a figure: "Your savings of ₹Y more than cover this in [Z] months".
  - The baseline prompt doesn't override it; the rule exists only in the inactive `GUARDED_ADDENDUM`.

**Evidence:**
- Raw outputs per case, in [`transcripts.md`](20261010T230941Z_off/transcripts.md).
- Playbook text from `get_advisor_context` (`discovery/raw/context__advisor_full.json`): "3. Show the cost: \"Joining fee: ₹X (incl. GST). Your savings of ₹Y more than cover this in [Z] months\"".
- **Detector gaps** (our checker, not the bot): Q20's ₹7,820 and Q09's ₹12,000 passed because the same numbers happen to appear in the tool output (Swiggy BLCK net "₹7,820"; HSBC Premier fee "₹12,000 + GST").

**Smallest corrective action:** a system-prompt rule that overrides the playbook: no calculated ₹ figures; say which figure isn't available and show the returned parts. → **Task 4 candidate.**

**Regression tests:**
- Q20, Q05, Q07, Q09, Q11 and Q13 must produce no `unreturned_rupee` flag, and reviewers must check by hand for coincidental matches.
- Q20 adds `forbidden_phrases: ["₹7,820", "break-even", "Month 2"]`.
- Controls Q01, Q03 and Q10 must still quote the tool's figures (no over-refusal).

## E05: Online-only cashback credited to in-person dining (S2, MCP tool or Data)

**Question (Q02):** "I eat out at restaurants a lot, about ₹10,000 a month, always in person, not Zomato or Swiggy. Best card for that?"

**Answer:** "Runners-up … **BOB Cashback** and **CRED IndusInd:** about ₹5,400/year net each." SBI Cashback was #5 in the tool's list.

**What's wrong:**
- **Expected:** cards whose 5% applies only online earn their offline rate on restaurant bills.
- **Actual:** 5% is credited, which overstates these cards by ₹4,800/yr on SBI Cashback's 1% offline rate.
- **Q13 T2:** SBI Cashback's ₹12,000 #1 includes ₹3,000/yr of in-person dining at 5%.
  - At 1% it would be about ₹9,600, a tie with HDFC Millenia's returned ₹9,600.
  - The headline "SBI Cashback is the best" therefore depends on this defect. (These are reviewer calculations, not bot output.)

**Cause:**
- **Symptom (high confidence):** the tool's figures contradict its own key definition and the cards' terms.
  - `dining_or_going_out` is "IN-PERSON dining only" (input description).
  - SBI and BOB terms limit 5% to online.
- **Root-cause location: inconclusive.** It could be the engine mapping `dining_or_going_out` to an online bucket, or card reward rules mis-tagged in the data. Both give the same output.
- **CRED IndusInd's terms were not fetched,** so it's listed on the tool's evidence only.

**Evidence:**
- Q02 `recommend_cards{"dining_or_going_out":10000,…}` → BOB Cashback, CRED IndusInd and SBI Cashback each `"annual_rewards_value": "₹6,000"` (5% × ₹1,20,000).
- Input description: "dining_or_going_out … This is IN-PERSON dining only."
- SBI Cashback terms (`get_card_details`, Q03/Q07): "Get 5% Cashback on Dining — Restaurant Payments processed through online platforms" and "1% on offline spends".
- BOB Cashback terms (`discovery/raw/followup__details_bob_cashback.json`): "Earn 5% Cashback … on online spends on all eligible domestic online purchases, capped at ₹1,500 per month".

**Evidence still to collect:**
1. `get_card_details{"card_alias":"cred-indusind-bank-credit-card"}` (one call) for its dining terms.
2. From engineering: the reward rule each of these cards applies to `dining_or_going_out`. That settles engine vs data.

**Smallest corrective action:** apply each card's offline or in-person rule to `dining_or_going_out` (server).

**Regression test (server):** `recommend_cards{dining_or_going_out:10000}` must give SBI Cashback 1% (₹1,200/yr), not ₹6,000.

## E06: `net_annual_savings` leaves out the joining fee (S2, MCP tool)

**Question (Q20 T2):** "Does the savings figure from the tool already subtract the joining fee?"

**Answer:** "No. The tool's ₹9,000 doesn't subtract the joining fee." The bot gets this right.

**What's wrong:**
- **Expected:** what the tool description promises, "NET ANNUAL SAVINGS (rewards earned + lounge value + milestone benefits - joining fee - annual fee)".
- **Actual:** the joining fee is never subtracted. As a result:
  - Millenia (₹1,180 joining fee) ties with the free ICICI Amazon Pay at ₹9,000 and is ranked #1 (Q01, Q15).
  - The bot's "first-year savings" maths (E04) was a reaction to this gap.

**Cause:** MCP tool, high confidence. The tool description and its behaviour conflict, which is the assignment's own example of this class.

**Evidence:**
- `recommend_cards` description (`discovery/tools.json`): "ranks by NET ANNUAL SAVINGS (rewards earned + lounge value + milestone benefits - joining fee - annual fee)".
- Response `_format_hint`: "net_annual_savings = annual_rewards + milestone_benefits + lounge_value - annual_fee".
- Q20 Millenia row: `"net_annual_savings": "₹9,000", "annual_rewards_value": "₹9,000", "joining_fee": "₹1,180 (incl. GST)"`.

**Smallest corrective action:** either subtract the joining fee (first-year net), or rename the field and fix the description. Ideally return both `first_year_net` and `ongoing_annual_net`.

**Regression test (server):** for `amazon_spends=15000`, Millenia's first-year net = ₹7,820 and ICICI Amazon Pay's = ₹9,000, so ICICI ranks above Millenia.

## E07: `annual_value` holds monthly figures, and the bot reads them as yearly (S2, Mixed: MCP tool → Model)

**Question (Q05):** "I pay ₹30,000 rent every month through CRED. Which credit card gives me the best rewards on rent?"

**Answer:** "The best rent earner I found is the **IDFC FIRST WOW! Black**, and even it earns only about **₹400 a year** on ₹30,000/month of rent." Then: "Paying rent on this card would cost you money."

The same misread appears in:
- **Q06:** "only ₹75 a year from Amazon on the top card"; "about ₹375 a year".
- **Q07 T2:** "The tool's own breakdown shows just ₹40 a year from Amazon, ₹30 from grocery and ₹20 from Flipkart."

**What's wrong:**
- **Expected:** rent rewards of ₹4,800/yr (the card's `annual_rewards_value`).
- **Actual:** "₹400 a year", 12× too low. The answer's conclusion is built on that number.

**Cause:**
- **Root (MCP tool, high confidence):** `top_spend_categories[].annual_value` holds monthly values in every response checked.
- **Contributing (Model):** it believed the label. The model can read the field correctly, as in Q03's "₹750/month", so the misread is inconsistent rather than unavoidable.

**Evidence:**
- Q05 row: `"annual_rewards_value": "₹4,800", "top_spend_categories": [{"category": "rent", "annual_value": "₹400"}]` (400 × 12 = 4,800).
- Same pattern elsewhere:
  - Q02 HSBC Live+: dining `"₹1,000"` vs `annual_rewards_value` `"₹12,000"`.
  - Q03 SBI Cashback: Amazon `"₹750"` = 5% × ₹15,000/month.
  - Discovery: holds for every scenario (FINDINGS §4).

**Smallest corrective action:**
- **Server:** rename the field to `monthly_value`, or multiply by 12.
- **Bot:** a prompt note that this field is monthly. This states a verified fact about the server and hides no defect.

**Regression test:** Q05 `forbidden_phrases: ["₹400 a year"]`. Server: `annual_value` × 1 summed over categories ≈ `annual_rewards_value`.

## E08: Joining fee described as waived (S2, Model)

**Question (Q01):** "I spend ₹15,000 a month on Amazon. Which card gives me the most back?"

**Answer:** "**HDFC Millenia**: ₹1,180 joining fee (incl. GST), waived when you spend ₹1 lakh a year, which you'd reach."

**What's wrong:**
- **Expected:** the ₹1,180 joining fee is always paid; the ₹1 lakh waiver applies to the annual fee.
- **Actual:** the user is told a real charge goes away.

**Cause:** Model, high confidence. The tool output separates the two fees without ambiguity.

**Evidence:**
- Q01 `recommend_cards` row: `"joining_fee": "₹1,180", "annual_fee": "Free (waived — ₹1,180 waived at ₹1,00,000/yr spend)"`.
- Q20 `get_card_details`: "The annual fee is waived if you spend ₹1 lakh or more in a year on your card".

**Smallest corrective action:** a prompt rule: always state the joining fee and the annual fee separately, and attach a waiver only to the annual fee unless the tool says otherwise.

**Regression test:** Q01 `forbidden_phrases: ["joining fee (incl. GST), waived", "joining fee is waived"]`.

## E09: Invented explanation for a tool figure (S2, Model)

**Question:** as in E07.

**Answer:** "**The ₹4,800 net savings figure** for the WOW Black comes from other spending the tool assumed, not from rent. Please don't read it as a rent reward."

**What's wrong:** the tool assumed nothing; rent was the only input. The bot made up a reason to explain away the contradiction its own misread (E07) created.

**Cause:** Model, high confidence.

**Evidence:** the request was `recommend_cards{"rent": 30000, "response_format": "full", "top_n": 5}`, with no other spend keys.

**Smallest corrective action:** a prompt rule: when tool figures seem inconsistent, say so; never attribute assumptions to the tool that aren't in its output.

**Regression test:** Q05 `forbidden_phrases: ["the tool assumed"]`.

## E10: Lounge rows contradict themselves (S3, Mixed: MCP tool → Model)

**Question (Q08):** "I fly domestic a lot: about ₹3 lakh a year on flights, ₹1.5 lakh a year on hotels, and I use airport lounges about 2 times every quarter. Eating out ₹15,000 a month. Best travel card?"

**Answer:** "**Lounges:** 8 domestic visits per quarter, well above your 2", said for Magnus Burgundy and Diners Black Metal.

**What's wrong:**
- **Expected:** describe the card's real lounge benefit and condition. Magnus has "Unlimited Domestic Airport Lounge Access on spending ₹50,000 in the previous 3 months".
- **Actual:** "8 per quarter", a number that is the user's own usage per year.

**Cause:**
- **Root (MCP tool, high confidence):** each row contradicts itself.
  - The visit count is labelled per quarter but holds visits per year, capped by the user's usage.
  - The rupee value covers only one quarter (C2).
- **Contributing (Model):** it believed the label and didn't use the card's terms.

**Evidence:**
- Q08 (usage 2/quarter): `"lounge_value": "₹1,500", "lounge_access": {"domestic_per_quarter": 8, "domestic_value_used": "₹1,500"}`. The visit count is 8 (2 × 4); the value is 2 × ₹750 (one quarter).
- Q09 (usage 1/quarter): Kotak Solitaire (unlimited) `"international_per_quarter": 4, "international_value_used": "₹1,250"`. That's 4 visits, valued as 1 × ₹1,250.
- Input description: "Valued at ₹1,250 per visit".
- Effect in Q09: every card is valued at ₹1,250 whether it allows 2 or 4 visits, which changes the order of the lounge ranking.

**Smallest corrective action (server):** report annual visits and value them annually (count × 4 quarters × per-visit value), with honest field names.

**Regression test (server):** `domestic_lounge_usage_quarterly=2` on an unlimited card → 8 visits/yr, ₹6,000.

## E11: "No lounge access" said of a card that has it (S3, Mixed: Model → MCP field naming)

**Question (Q06 T2/T3):** "I also spend ₹10,000 a month eating out at restaurants, in person, and ₹1 lakh a year on flights. Does that change your recommendation? Why?" Then: "What's the best second card for me?"

**Answer:** T2: "**None of the top 5 include lounge access**, even with ₹1 lakh a year on flights." T3 (ixigo AU): "**Lounge access:** None."

**What's wrong:** ixigo AU's terms give "8 complimentary domestic airport lounge visits per year … on a minimum spend of ₹50,000 in the previous calendar quarter" and 1 international visit.

**Cause:**
- **Model, high confidence:** the zeros reflect *usage* (no lounge usage was entered; the sibling field is `domestic_value_used: "₹0"`), not the card's benefit.
- **Contributing (MCP naming):** the field name `lounge_access` invites the misreading.

**Evidence:**
- Q06 ixigo row: `"lounge_value": "₹0", "lounge_access": {"domestic_per_quarter": 0, …, "domestic_value_used": "₹0"}`.
- Card terms: `get_card_details{"card_alias":"ixigo-au-credit-card"}` in Q07.

**Smallest corrective action:** a prompt note: lounge fields in `recommend_cards` reflect entered usage; use `get_card_details` before claiming a card has or lacks lounges.

**Regression test:** Q06 `forbidden_phrases: ["None of the top 5 include lounge"]`.

## E12: Prime-rate cashback assumed with no input or caveat (S3, Mixed: MCP tool → Model)

**Question (Q01):** as in E08.

**Answer:** "**ICICI Amazon Pay Credit Card**: Free joining and annual fee … The ICICI Amazon Pay card gives the same savings with no fees, so I'd start there."

**What's wrong:**
- **Expected:** ₹9,000 holds only for Prime members. The card's data gives 3% (₹5,400 on ₹1.8L) for non-Prime.
- **Actual:** the bot recommends it first without the condition.

**Cause:**
- **Root (MCP tool, high confidence):** the engine applies the Prime rate and has no Prime input.
- **Contributing (Model):** the caveat is missing, though the tools' "Up To 5%" wording was available (Q11, Q13).

**Evidence:**
- Q01 row: `"net_annual_savings": "₹9,000"`.
- `discovery/raw/cards__details_icici_amazon_pay.json`: "5% unlimited cashback on Amazon purchases for Prime members … 3% unlimited cashback on Amazon purchases for non-Prime members".

**Smallest corrective action:**
- **Server:** add an `amazon_prime` input, or return both rates.
- **Bot:** state the Prime condition whenever ICICI Amazon Pay is named.

**Regression test:** Q01 `required_any` [["Prime"]] when ICICI Amazon Pay is in the answer.

## E13: Rent rewards credited, rent fee ignored (S3, MCP tool, medium confidence)

**Question / answer:** as in E07.

**What's wrong:**
- **Expected:** rent on IDFC WOW Black costs a 1% fee, about ₹3,600/yr on ₹3.6L (reviewer arithmetic). That cancels most of the ₹4,800 reward.
- **Actual:** `net_annual_savings` shows ₹4,800 with no deduction.
- **In this case the bot warned about the fee anyway (wrongly, see E07), so the user was protected by accident.**

**Cause:**
- **MCP tool, medium confidence:** the formula only subtracts annual fees.
- **This isn't a description conflict:** the stated formula has no transaction-fee term. It's a modelling gap that makes "net" misleading for rent.
- **The ₹4,800 reward figure itself couldn't be checked.** The card's terms returned here don't give a rent earn rate.

**Evidence:**
- Q05 row: `"net_annual_savings": "₹4,800", "annual_rewards_value": "₹4,800"`.
- Q05 `get_card_details{"card_alias":"idfc-first-wow-black-credit-card"}` → `fee_schedule.rent_payment_fee: "1%"`.

**Evidence still to collect:** the card's rent earn rate (issuer MITC) to verify ₹4,800.

**Smallest corrective action (server):** subtract `fee_schedule` charges for categories the engine rewards (rent, and likely fuel and utilities), or flag them.

**Regression test (server):** `rent=30000` → IDFC WOW Black net reflects the 1% fee.

## E14: Wouldn't rank on a single category (S3, Mixed: MCP guidance → Model)

**Question (Q06 T1):** "I spend ₹15,000 a month on Amazon. Best card?"

**Answer:** "To rank the options properly, I need a rough monthly figure for a few more categories:" followed by five questions and no ranking.

**What's wrong:**
- **Expected:** answer the question that was asked, as Q01 did for the same spend, then offer to refine.
- **Actual:** no recommendation.

**Cause:**
- **Root (MCP guidance, high confidence):** the playbook the bot loads every turn says "MINIMUM REQUIRED: at least 2 spending categories with amounts before calling recommend_cards".
- **Contributing (Model):** it applies that rule inconsistently. Q01 answered.

**Evidence:**
- Q06 T1 trace: only `get_advisor_context{"topic":"full"}`.
- Playbook text: `discovery/raw/context__advisor_full.json`.

**Smallest corrective action:** a prompt rule: if the user gives at least one spend amount, rank first, then ask follow-ups.

**Regression test:** Q06 T1 `must_call: recommend_cards`.

## E15: Invalid pincode returns 0 cards with no error (S3, MCP tool)

**Question (Q16 T2):** "My pincode is 123456."

**Answer:** "no cards in our database are currently available to you." The bot sensibly asked the user to confirm the pincode.

**What's wrong:**
- **Expected:** a validation error for a pincode that doesn't exist.
- **Actual:** a well-formed empty result. A less careful client would tell the user they qualify for nothing.

**Cause:** MCP tool, high confidence. The same happens for `000000` (discovery).

**Evidence:**
- `check_eligibility{"pincode":"123456",…}` → `{"eligible_cards_count": 0, …, "eligible_cards": []}` with no error field.
- Discovery: `eligibility__invalid_pincode`, `p2__elig_123456_self_6L`.

**Smallest corrective action (server):** return `isError` with "unknown pincode".

**Regression test (server):** pincodes `123456` and `000000` → error.

## E16: Unsupported reasoning stated as fact (S3, Model)

| Case | Answer excerpt | What the tool output shows |
|---|---|---|
| Q01 | "Swiggy Ornge … Its savings are mainly from Swiggy, so it's less useful if you don't order food on Swiggy." | Only `amazon_spends` was passed, so its ₹9,000 is all from Amazon |
| Q06 T2 | "₹1 lakh a year on flights is the largest factor." | Amazon ₹1.8L/yr and dining ₹1.2L/yr are larger; flights add ₹208/month on #1 |
| Q08 | "The Diners Black Metal gives nearly the same value for about a third of the fee." | ₹76,700 vs ₹97,320 is 21% lower |
| Q07 T1 | "**1. SBI Cashback Credit Card (best for your spend)** … about ₹13,200/year … **2. HSBC Live+** … about ₹14,160/year" | Reverses the tool's order with no returned basis ("I haven't pulled its full terms yet") |

- **Cause:** Model, high confidence. Each claim contradicts, or isn't supported by, the turn's own tool output.
- **Smallest corrective action:** a prompt rule: every "because" must point to a returned field; keep the tool's order unless a returned field justifies changing it.
- **Regression test:** the review checklists on Q01, Q06, Q07 and Q08 (human review). These claims aren't machine-detectable today.

## E17: Missing caveats and unstated assumptions (S3–S4, Model)

| Case | Gap | Evidence |
|---|---|---|
| Q16 T3 | "you're eligible for **231 cards**", with no "indicative" | `check_eligibility` count 231 (see E01) |
| Q09 | Never says the engine has no overseas-spend input. Its ranking was lounge-only | `recommend_cards{"international_lounge_usage_quarterly": 1, "flights_annual": 0, …}` |
| Q13 T1 | Stated the Amazon Pay ICICI assumption but silently picked regular Magnus over Burgundy. The user had to correct it in T2 | `compare_cards{["axis-bank-magnus-credit-card", …]}`; `magnus-burgundy-credit-card` exists (Q08) |
| Q04 (S4) | Sent Netflix/Spotify as `other_online_spends` without saying so; called ixigo "Free (lifetime)" where the tool says "Free" | Q04 request and row |

- **Smallest corrective action:** prompt rules: state every assumption and mapping; call eligibility indicative.
- **Regression tests:** add `required_any` ["indicative"] to Q16 T3. The rest stay on the review checklist.

---

## Tool and data defects the bot worked around (answers passed)

| Defect | Class | Confidence | Evidence |
|---|---|---|---|
| `list_cards` ignores `free_cards` and `annual_fees` (Q14, Q17); discovery found every filter except `category` ignored | MCP tool | High | `list_cards{"free_cards":"true","annual_fees":"free"}` → `total_available: 258` (= unfiltered) and returns SBI Cashback ₹1,179 … HSBC Taj ₹1,29,800. The description maps "lifetime free" → `free_cards="true"`. The bot filtered by hand to 7 cards free on both fees. |
| Resolver reports "high" confidence for a card from another bank (Q12) | MCP tool | High | `whatsapp_resolve_card_or_category{"phrase":"HDFC Platinum Ultra Max"}` → `"name": "RBL Platinum Maxima Credit Card", "confidence": "high"`. The bot refused it. |
| `bank` is empty in list, eligibility and resolver rows | MCP tool | High | `"bank": ""` on every row (Q09, Q14–Q17, Q12) |
| Unrounded money strings | MCP tool | High | `"annual_rewards_value": "₹1,31,219.997"` (Q08) |
| Structured milestones are null while the text describes them | Data | High | Landmark, Regalia Gold, Millenia: `[{"spend_target": null, …}]` |

## Inconclusive: evidence to collect

| Item | Why it's open | Evidence needed |
|---|---|---|
| `existing_customer_only: true` on SBI Cashback, HDFC Millennia, HSBC Live+ (Q02, Q03, Q20) | Contradicts `new_to_credit: true` on some of the same cards (discovery). Real-world truth isn't in the tool data | Issuer product and application pages for each card |
| Scapia listed under `"bank": "Axis"` (Q09) | Only outside knowledge says otherwise | Scapia's issuer from its official site or MITC |
| E05 root location (engine vs data) | Identical output either way | CRED IndusInd `get_card_details`, and the server's dining rule per card |
| E03 Landmark ₹30,000 mechanism | ₹2.50/point matches no conversion in the card's data | The stored milestone record for `sbi-landmark-reward-select-credit-card` |
| ICICI Emeralde in Q16's ₹6 LPA list | Its income floor wasn't fetched | `get_card_details{"card_alias":"icici-emeralde-credit-card"}` |
| E13 reward side | No rent earn rate in the returned terms | IDFC WOW Black MITC |

## Our checker's limits (not product failures)

- **False positives (excluded from the findings above):**
  - Sums or ×12 of the user's own numbers: ₹17,000, ₹2.04 lakh, ₹28,300, ₹22,000, ₹2.4L, ₹8 lakh.
  - Rounding: ₹5,400, ₹9,600, ₹17,400.
- **False negatives, caught only in human review:**
  - E01 (eligibility promise)
  - E02 (tax wording)
  - E04 coincidental matches (₹7,820, ₹12,000)
  - E07, E09, E16 (semantic errors)
- **Nondeterminism:** even at temperature 0, the smoke run's fee-waiver answer (S01) was wrong while the same question here (Q03) was right, and Q01 and Q06 T1 behaved differently on the same input. Before/after comparisons need reruns, not one sample.
