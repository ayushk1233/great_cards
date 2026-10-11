# Engineering handoff: MCP server and data issues

**Status:** proposals only. The production MCP server was not changed, and no extra probes were sent to write this. Every figure below comes from tool outputs already recorded in this repo.
**Server:** `https://bk-api.bankkaro.com/mcp`, version 1.6.1 (catalog hash `0600faf19c22`).
**Scope:** server-side and data-side problems only. Chatbot (model) fixes are in [fixes_before_after.md](fixes_before_after.md).

- **Part A**: the top-priority issue (E01, eligibility), as a full spec.
- **Part B**: every other server or data problem, with evidence and a possible solution.
- **Part C**: items that need more investigation before a fix can be specified.

---

# Part A. Top issue: `check_eligibility` doesn't apply card income floors (E01)

**Severity:** S1, harmful advice. **Confidence:** high that the defect exists; medium on its mechanism.

## 1. Problem statement

`check_eligibility` lists cards whose income requirement, stored in the same server's `get_card_details`, is well above the income it was given. Its description promises "which cards a user can actually APPLY for based on pincode, **income**, and employment". At ₹6 lakh/year it returns HDFC Regalia Gold, whose own record requires ₹18 LPA, and that holds for both salaried and self-employed. At ₹1 lakh/year it returns cards that require ₹3–4 LPA.

So the bot tells users they qualify for cards the server's own data rules out. A user who acts on that applies for a card they don't qualify for.

### Why this issue, out of the server-side findings

| Finding | Harm | Confidence | Can the bot work around it? |
|---|---|---|---|
| **E01 eligibility ignores income floors** | **S1**: "yes, you're eligible" when the card's terms say no | **High**: two tools on the same server contradict each other | **Only for one named card**, at the cost of an extra `get_card_details` call. For "which cards can I get?" it would need up to 232 detail calls, far beyond the rate limit (about 65 per 3 min). Q16 still fails in the final run. |
| E03 milestone overvaluation | S2: wrong #1 card | High on the symptom, medium on the mechanism | Partly: the bot can caveat it, but can't recompute a value |
| E05 online-only dining credited for in-person dining | S2 | High on the symptom; engine vs data unknown | Caveat only |
| E06 net savings leave out the joining fee | S2 | High | Yes: the bot shows both returned figures (F1) |
| E10 lounge label | S3 | High | Partly |

E01 is the only server defect that is S1, high-confidence, and beyond what the bot can fix at the scale the tool is used.

## 2. Tool contract (as published by the server)

From `tools/list` (`discovery/tools.json`):

- **Description:** "Check which cards a user can actually APPLY for based on pincode, income, and employment."
- **Inputs:**
  - `pincode`: 6-digit string.
  - `annual_income`: string, described as "Annual in-hand income in ₹ … (e.g. "1200000" for 12 LPA)".
  - `employment_status`: `salaried` or `self_employed`.
- **Output** (verified): `eligible_cards_count`, `profile`, and 15 `eligible_cards` rows (no pagination). Each row carries `name`, `bank`, `joining_fee`, `annual_fee`, `rating`, `invite_only`, `employment_type`, `new_to_credit`, `key_benefits`, `tags`, `card_alias`, `image`. **No row carries an income requirement, a reason, or an "indicative" flag.**

Source data for the same card, from `get_card_details`:

```json
"eligibility": {
  "min_age": 21, "max_age": 60,
  "income_salaried_lpa": 18, "income_self_emp_lpa": 18,
  "min_income_monthly": 150000,
  "crif_salaried": 750, "crif_self_emp": 750
},
"card_alias": "hdfc-regalia-gold"
```

(The final-run Q15 trace and `discovery/raw/cards__details_regalia_gold_a.json` are identical.)

## 3. Reproducible example (observed, not constructed)

### 3a. The case that hurt a user: Q15

**User:** "I'm salaried with a CTC of ₹6 lakh a year, pincode 400001. Am I eligible for the HDFC Regalia Gold?"

**Request:**
```json
check_eligibility {"pincode": "400001", "annual_income": "600000", "employment_status": "salaried"}
```

**Response** (identical in the baseline run, the final run and discovery `eligibility__mumbai_6L_salaried`):
```json
{
  "eligible_cards_count": 232,
  "profile": {"pincode": "400001", "annual_income": "₹6,00,000", "employment": "salaried"},
  "eligible_cards": [ …,
    {"name": "HDFC Regalia Gold Credit Card", "joining_fee": "₹2,950 (₹2,500 + GST)",
     "annual_fee": "₹2,950 (₹2,500 + GST)", "employment_type": "both", "card_alias": "hdfc-regalia-gold", …},
  … ]
}
```
Regalia Gold is row 6 of 15.

**Baseline bot answer** ([`20261010T230941Z_off`](20261010T230941Z_off/transcripts.md)): "**Yes, you're eligible for the HDFC Regalia Gold** based on your ₹6 lakh salary and Mumbai pincode 400001."

### 3b. More observed calls showing the same defect

| Request (pincode, income, employment) | `eligible_cards_count` | Rows that contradict the card's own floor | Source |
|---|---|---|---|
| 400001, ₹6,00,000, salaried | 232 | `hdfc-regalia-gold` (floor 18 LPA) | Q15 baseline and final; `eligibility__mumbai_6L_salaried` |
| 110001, ₹6,00,000, self_employed | 231 | `hdfc-regalia-gold` (self-employed floor 18 LPA) | Q16 T3 baseline and final; `p2__elig_delhi_self_6L` |
| 848101, ₹3,00,000, salaried | 200 | `hdfc-regalia-gold` (18 LPA) | `followup__elig_rural_3L_salaried` |
| 400001, ₹1,00,000, salaried | 201 | `sbi-cashback-credit-card` (3 LPA), `axis-flipkart-credit-card` (3 LPA), `hdfc-millenia-credit-card` (4 LPA) | `followup__elig_mumbai_1L_salaried` |
| 400001, ₹25,00,000, salaried | 232 | none visible; same 232 as at ₹6 L | `eligibility__mumbai_25L_salaried` |
| 110001, ₹0, salaried | 3 | SBM Kredit.Pe, SBM ZET, IDFC FIRST WOW (floors not fetched) | `p2__elig_delhi_income_0` |

The floors used above all come from `get_card_details` responses recorded in `discovery/raw/`:

| Card | `income_salaried_lpa` | `income_self_emp_lpa` | `min_income_monthly` |
|---|---|---|---|
| hdfc-regalia-gold | 18 | 18 | 150000 |
| hdfc-millenia-credit-card | 4 | 6 | 35000 |
| sbi-cashback-credit-card | 3 | 3 | 30000 |
| axis-flipkart-credit-card | 3 | 3.5 | 25000 |

**What the counts show:** the income input does have *some* effect (₹0 → 3 cards, ₹1 L → 201, ₹6 L → 232), but ₹6 L and ₹25 L return the same 232. A filter on these floors would drop Regalia Gold at ₹6 L, and SBI Cashback, Axis Flipkart and Millenia at ₹1 L. It does neither.

### 3c. Actual vs expected

| Input | Card | Card's floor (own record) | Actual | Expected |
|---|---|---|---|---|
| ₹6,00,000 salaried | HDFC Regalia Gold | ₹18,00,000 (18 LPA) | Listed as eligible | **Not listed** |
| ₹6,00,000 self-employed | HDFC Regalia Gold | ₹18,00,000 | Listed | **Not listed** |
| ₹6,00,000 self-employed | HDFC Millenia | ₹6,00,000 (6 LPA) | Listed | **Listed** (meets the floor exactly) |
| ₹3,00,000 salaried | HDFC Regalia Gold | ₹18,00,000 | Listed | **Not listed** |
| ₹1,00,000 salaried | SBI Cashback / Axis Flipkart / HDFC Millenia | ₹3,00,000 / ₹3,00,000 / ₹4,00,000 | Listed | **Not listed** |
| ₹18,00,000 salaried | HDFC Regalia Gold | ₹18,00,000 | not tested | **Listed** (if the pincode is serviceable; 400001 is, since the card is listed there today) |

## 4. Proposed correction

### 4.1 Filter (core fix)

For each card, after the existing pincode and employment filters:

```
floor_lpa = card.eligibility.income_salaried_lpa   if employment_status == "salaried"
            card.eligibility.income_self_emp_lpa   if employment_status == "self_employed"
floor_rupees = round(floor_lpa * 100000)            # integer rupees; LPA values can be decimal (2.4, 3.5)
if floor_lpa is null:
    floor_rupees = card.eligibility.min_income_monthly * 12   if present
include card  iff  int(annual_income) >= floor_rupees          # inclusive at the boundary
if no floor is known: include the row, with income_check = "unknown" (never silently "eligible")
```

### 4.2 Response contract (additive only; existing fields unchanged)

- **Per row:**
  - `min_income_required` (e.g. `"₹18,00,000"`);
  - `income_check`: `"meets"` or `"unknown"`.
- **Top level:**
  - `criteria_checked: ["pincode", "income", "employment"]`;
  - `criteria_not_checked: ["credit_score", "age", "existing_relationship"]`. The tool has no credit score or age input, yet Regalia Gold needs CRIF 750 and ages 21–60;
  - `note: "Indicative only; the issuing bank makes the final decision."`

These additions let any client, not just ours, avoid turning a list row into a promise.

### 4.3 Input validation (same tool, small)

A non-numeric `annual_income` (`"50k"`) currently returns `"annual_income": "₹NaN"` with 0 cards and `isError: false` (`followup__elig_income_50k_string`). It should return `isError: true` with "annual_income must be digits only, in ₹ per year". This is separate from the core fix and can ship independently.

### 4.4 Decisions needed from product/data before shipping

1. **Which field is authoritative when they disagree.** `min_income_monthly × 12` doesn't always match the LPA fields: SBI Cashback gives 30,000 × 12 = ₹3.6 L vs 3 LPA; Millenia 35,000 × 12 = ₹4.2 L vs 4 LPA salaried. The proposal uses the employment-specific LPA field because it distinguishes salaried from self-employed. Data owners should confirm.
2. **In-hand vs gross.** The input asks for "Annual in-hand income", but bank floors in LPA are usually stated on gross income. Comparing in-hand to gross under-qualifies users. Either change the input description to gross annual income, or document the conversion. Don't change it silently.

## 5. Acceptance tests

Run against staging or a fixture of the card database, **not production**. Case IDs refer to the inputs in §3.

| # | Input `(pincode, annual_income, employment)` | Expected |
|---|---|---|
| A1 | `400001, "600000", salaried` | `hdfc-regalia-gold` **absent** |
| A2 | `400001, "1800000", salaried` | `hdfc-regalia-gold` **present** (boundary inclusive) |
| A3 | `400001, "1799999", salaried` | `hdfc-regalia-gold` **absent** |
| A4 | `110001, "600000", self_employed` | `hdfc-regalia-gold` **absent**; `hdfc-millenia-credit-card` **present** (self floor 6 LPA) |
| A5 | `110001, "599999", self_employed` | `hdfc-millenia-credit-card` **absent** |
| A6 | `400001, "100000", salaried` | `sbi-cashback-credit-card`, `axis-flipkart-credit-card`, `hdfc-millenia-credit-card` **all absent** |
| A7 | `400001, "300000", salaried` | `sbi-cashback-credit-card`, `axis-flipkart-credit-card` **present** (floor 3 LPA); `hdfc-millenia-credit-card` **absent** (4 LPA) |
| A8 | **Invariant, full catalogue:** incomes {0, 1 L, 2.4 L, 3 L, 6 L, 18 L, 25 L} × both employments × {400001, 110001} | Every returned row with `income_check="meets"` has `min_income_required ≤ annual_income`; no card with a known floor above the income is returned |
| A9 | **Monotonicity**, same pincode and employment | The eligible set at a lower income is a subset of the set at a higher income. After the fix, the ₹6 L count is **below** the ₹25 L count (today both are 232) |
| A10 | **Cross-tool consistency:** for every row returned by A8 | `get_card_details(card_alias).eligibility` floor for that employment ≤ the input income |
| A11 | **Contract:** every field in today's response | Same name and type; new fields only added |
| A12 | `400001, "50k", salaried` | `isError: true` with a message (if 4.3 ships); never `₹NaN` with 0 cards |
| A13 | **Regression guard:** pincodes `123456`, `000000` | Unchanged from today's behaviour (0 cards). That's a separate finding (E15) and is out of scope here |

**Chatbot regression check after the server ships:** rerun Q15 and Q16 (`python -m app.evaluation.runner --mode prompt --only Q15 Q16`, about 15 MCP requests).
- **Q15:** Regalia Gold should no longer appear in the eligibility rows. The bot should then answer "not on these numbers" from the eligibility tool itself, rather than from its cross-check against the card details.
- **Q16 T3:** shouldn't list Regalia Gold, and the count should drop.

## 6. Regression risks

| Risk | Why | Mitigation |
|---|---|---|
| **Eligible counts fall sharply** | Users and flows that show "you're eligible for N cards" will see much smaller N. `recommend_cards`' documented "IDEAL FLOW: check_eligibility first" will pass fewer cards on | Expected and correct, but flag it to product/UX before release |
| **Good applicants excluded by bad floor data** | Inconsistent or stale floors (see 4.4.1) now exclude cards, where today they're ignored | Audit floors first; until then, ship the floor in the response (4.2) behind a flag before turning on the filter |
| **Cards with missing floors** | Null fields could silently include or exclude cards | `income_check: "unknown"`, never treated as "meets" |
| **Unit errors** | LPA (lakhs) vs rupees vs monthly; decimal LPA (2.4, 3.5) | Compare in integer rupees; tests A2/A3/A5 pin both boundaries |
| **In-hand vs gross mismatch** | Under-qualifies salaried users | Resolve 4.4.2 before release |
| **Shared filter code** | There's no WhatsApp eligibility tool, but `recommend_cards` and the `whatsapp_recommend_*` tools may reuse the same card-filter code | Run their existing tests; confirm their rankings for a fixed profile don't change unless they're meant to apply eligibility |
| **Row order changes** | Only 15 rows are returned, so removing cards changes which 15 users see | Acceptable; note it in the release notes |
| **Chatbot rules written against today's behaviour** | Our prompt rules don't encode eligibility behaviour, but the answers to Q15 and Q16 will change | Rerun Q15 and Q16 (§5) |

## 7. Remaining uncertainty

- **Mechanism (medium confidence).** The income input clearly does *something*: Regalia Gold is absent from the visible ₹1 L rows (the rest of the list keeps the same order) but present at ₹3 L. Its effective cut-off therefore sits between ₹1 L and ₹3 L, not at ₹18 L. Two explanations fit every observed call:
  - (a) annual income is compared with `min_income_monthly` (₹1,50,000) without ×12;
  - (b) LPA is converted with the wrong multiplier (18 × 10,000 = ₹1,80,000).

  **I haven't tested which one it is.** A code read settles it immediately. From outside, it would take two boundary calls for Regalia Gold, at ₹1,60,000 (passes under (a), fails under (b)) and ₹1,40,000. I haven't sent these, because production calls need your approval.
- **Extent.** Only 15 of the 200+ rows are visible per call, and floors were fetched for 12 cards. The full number of wrongly included cards at each income is unknown. Engineering can count them with one query against the card table (test A8).
- **Real-world floors.** The defect is the internal contradiction between `check_eligibility` and `get_card_details`. I haven't checked whether 18 LPA matches HDFC's current published criteria; that's a data-accuracy question for the data owner.
- **Credit score and age** aren't inputs, so they can't be checked. That's why the response should state "indicative" (4.2), rather than the tool claiming to cover them.
- **Bot-side mitigation is partial.** In the final run, Q15 passed: the bot fetched the card details and stated the contradiction. Q16 failed: it called 231 cards "eligible" and named Regalia Gold. A prompt rule ("eligibility is indicative; never say 'you're eligible for N cards'") is part of the Task 5 guardrails, still awaiting approval, but it can only soften the wording. It can't remove wrong cards from the list.

## Evidence index (Part A)

- Tool contract: `discovery/tools.json` (`check_eligibility`).
- Eligibility responses: `discovery/raw/eligibility__mumbai_6L_salaried.json`, `eligibility__mumbai_25L_salaried.json`, `followup__elig_mumbai_1L_salaried.json`, `followup__elig_rural_3L_salaried.json`, `p2__elig_delhi_self_6L.json`, `p2__elig_delhi_income_0.json`, `followup__elig_income_50k_string.json`.
- Card floors: `discovery/raw/cards__details_regalia_gold_a.json`, `cards__details_hdfc_millenia.json`, `cards__details_sbi_cashback.json`, `cards__details_axis_flipkart.json`.
- Bot transcripts: Q15 and Q16 in [`20261010T230941Z_off`](20261010T230941Z_off/transcripts.md) (before) and [`20261011T005033Z_prompt`](20261011T005033Z_prompt/transcripts.md) (after); reviews in each run's `review.md`.
- Finding write-up: [failures.md § E01](failures.md).

---

# Part B. Other MCP server and data problems

They're ordered by priority (harm, then how often they come up). Each one lists the problem, what was observed (from the recorded runs, with case IDs), a possible solution, and a test. Calculations marked "reviewer arithmetic" are ours, done to state an expected value; no tool returned them. Full write-ups are in [failures.md](failures.md).

## Summary

| # | Problem | Tool | Class | Sev | Cases | Confidence |
|---|---|---|---|---|---|---|
| B1 | Milestone bonus valued 5–10× the card's terms (E03) | `recommend_cards` | MCP tool / Data | S2 | Q04, Q06, Q07, Q11 | High on the symptom, medium on the mechanism |
| B2 | Online-only cashback credited to in-person dining (E05) | `recommend_cards` | MCP tool or Data | S2 | Q02, Q06, Q13 | High on the symptom |
| B3 | `net_annual_savings` leaves out the joining fee, contradicting the tool description (E06) | `recommend_cards` | MCP tool | S2 | Q01, Q15, Q20 | High |
| B4 | `top_spend_categories[].annual_value` holds monthly values (E07) | `recommend_cards` | MCP tool | S2 | Q05, Q06, Q07 | High |
| B5 | Lounge rows: annual visits labelled per quarter, value covers one quarter (E10) | `recommend_cards` | MCP tool | S3 | Q08, Q09 | High |
| B6 | Prime-only cashback rate applied with no Prime input (E12) | `recommend_cards` | MCP tool | S3 | Q01 | High |
| B7 | Transaction fees (rent 1%) not deducted from net savings (E13) | `recommend_cards` | MCP tool | S3 | Q05 | Medium |
| B8 | `list_cards` ignores every filter except `category` | `list_cards` | MCP tool | S3, plus cost | Q14, Q17 | High |
| B9 | Advisor playbook requires 2 categories and asks for un-returned payback figures (E14, E04) | `get_advisor_context` | MCP guidance | S3 | Q02, Q05, Q06 T1; E04 cases | High |
| B10 | `check_eligibility` input handling: bad pincode or income returns a silent 0; count without the rows (E15) | `check_eligibility` | MCP tool | S3 | Q16 | High |
| B11 | Resolver gives "high" confidence for a card from another bank | `whatsapp_resolve_card_or_category` | MCP tool | S3 | Q12 | High |
| B12 | Data quality: empty `bank`, null structured milestones, unrounded amounts, missing `card_type`, usage-based lounge field names | several | Data / contract | S3–S4 | many | High |

## B1. Milestone bonus overvalued (E03)

**Problem.** The milestone value in `recommend_cards` doesn't follow from the card's stated bonus points and point value. It's large enough to put a card at #1 for everyday profiles.

**Observed.**
- **Q07 `recommend_cards`**, SBI Landmark Reward SELECT, rank 1: `"net_annual_savings": "₹29,749", "annual_rewards_value": "₹1,518", "milestone_benefits": "₹30,000"`.
- **Same card's `get_card_details`:** "12,000 bonus Reward Points on overall annual retail spends of ₹3,00,000"; `point_value: "1 Reward Point = ₹0.25"`; structured `milestone_benefits: [{"spend_target": null, "reward": null, "description": null}]`.
- **ixigo AU:** milestone ₹20,000 in the tool. Its terms say "5,000 bonus Reward Points on ₹75,000+ spends per calendar quarter" at "1 Reward Point = ₹0.20".
- **The spend threshold works:** Landmark's milestone is ₹0 at ₹2,40,000/yr (rank 50) and ₹30,000 from ₹3,39,600/yr.

**Expected (reviewer arithmetic):**
- Landmark: 12,000 × ₹0.25 = **₹3,000**.
- ixigo AU: 5,000 × 4 × ₹0.20 = **₹4,000**.

**Possible solution:**
- Value each milestone as bonus points × that card's `point_value`.
- Fill the structured `milestone_benefits` record (`spend_target`, `reward`) from the terms, so the engine and clients read the same source.
- Return `milestone_spend_required` next to `milestone_benefits`, so clients can show that the value depends on reaching that spend.

**Test:**
- For the Q07 profile, Landmark `milestone_benefits` = ₹3,000, and Landmark is no longer rank 1.
- At ₹2,40,000/yr the milestone is still ₹0 (threshold behaviour kept).
- For every card with a milestone, `milestone_benefits` ≤ bonus points × `point_value`.

**Open:** whether the stored record or the engine formula is wrong. ₹30,000 equals ₹2.50 per point, which matches no conversion in the card's data. ixigo's ₹20,000 equals its points at ₹1 each. A code or database read settles it.

## B2. Online-only cashback credited to in-person dining (E05)

**Problem.** The input `dining_or_going_out` is described as "IN-PERSON dining only". Yet cards whose 5% applies only online are credited 5% on it.

**Observed.**
- **Q02** `recommend_cards{"dining_or_going_out": 10000, …}` → BOB Cashback, CRED IndusInd and SBI Cashback each `"annual_rewards_value": "₹6,000"` (5% of ₹1,20,000).
- **SBI Cashback terms:** "5% Cashback on Dining — Restaurant Payments processed through online platforms"; "1% on offline spends".
- **BOB Cashback terms:** 5% "on all eligible domestic online purchases".
- **Q13:** SBI Cashback's #1 position depends on this.

**Expected (reviewer arithmetic):** SBI Cashback at 1% offline on ₹1,20,000 = **₹1,200/yr**, not ₹6,000.

**Possible solution:**
- Map `dining_or_going_out` to each card's offline or in-person dining rule, and keep online-only rules for `online_food_ordering`.
- Audit the card reward rules for "online-only" tags on dining.

**Test:** `recommend_cards{dining_or_going_out: 10000}`:
- SBI Cashback `annual_rewards_value` = ₹1,200;
- no card whose terms limit dining cashback to online is credited above its offline rate.

**Open:** whether it's the engine mapping or the data tags; the output is identical either way. CRED IndusInd's terms weren't fetched.

## B3. `net_annual_savings` leaves out the joining fee (E06)

**Problem.** The tool description says net = "rewards earned + lounge value + milestone benefits - joining fee - annual fee". The response's own `_format_hint` and the returned numbers leave out the joining fee.

**Observed.**
- **Q20** HDFC Millenia: `"net_annual_savings": "₹9,000", "annual_rewards_value": "₹9,000", "joining_fee": "₹1,180 (incl. GST)"`.
- It ties with the free ICICI Amazon Pay at ₹9,000 and is listed #1 (Q01, Q15).

**Expected (reviewer arithmetic, per the description):** Millenia's first-year net = ₹7,820, which ranks below ICICI Amazon Pay's ₹9,000.

**Possible solution:**
- Return two fields: `first_year_net` (minus the joining fee) and `ongoing_annual_net` (minus the annual fee only). Rank on whichever the product chooses, and make the description match.
- At minimum, make the description and `_format_hint` agree with the formula actually used.

**Test:** for `amazon_spends=15000`:
- Millenia `first_year_net` = ₹7,820;
- ICICI Amazon Pay = ₹9,000;
- the description formula matches the computed fields for every row.

## B4. `annual_value` holds monthly figures (E07)

**Problem.** In `recommend_cards`, `top_spend_categories[].annual_value` is a monthly amount. Clients and models read it as yearly.

**Observed.**
- **Q05:** `"annual_rewards_value": "₹4,800"`, rent `"annual_value": "₹400"` (₹400 × 12 = ₹4,800). The baseline bot said "₹400 a year".
- The same pattern appears in Q02 (₹1,000 vs ₹12,000), Q03 (₹750 = 5% × ₹15,000/month), and every discovery scenario.

**Possible solution:** either rename the field to `monthly_value`, or multiply by 12 and keep the name. Then document it.

**Test:** for every row, the sum of `top_spend_categories[].annual_value` over the categories entered ≈ `annual_rewards_value`.

**Note:** chatbot rule F2 states the current behaviour. It must be removed when this ships.

## B5. Lounge rows contradict themselves (E10)

**Problem.** `lounge_access.*_per_quarter` holds a yearly visit count, capped at the user's usage. `*_value_used` and `lounge_value` cover only one quarter.

**Observed.**
- **Q08** (usage 2/quarter): `"lounge_value": "₹1,500", "lounge_access": {"domestic_per_quarter": 8, "domestic_value_used": "₹1,500"}`. That's 8 visits (2 × 4), valued as 2 × ₹750.
- **Q09** (usage 1/quarter), Kotak Solitaire: `"international_per_quarter": 4, "international_value_used": "₹1,250"`.
- The input description values visits "at ₹1,250 per visit". Every card gets the same value whatever its allowance, which changes the lounge ranking.

**Possible solution:**
- Report `domestic_visits_per_year` and `international_visits_per_year`, valued over the year: min(usage, card allowance) × 4 quarters × per-visit value.
- Keep the card's allowance and its spend condition as separate fields (B12).

**Test:** `domestic_lounge_usage_quarterly=2` on a card with unlimited domestic access gives 8 visits/yr and ₹6,000 (8 × ₹750).

## B6. Prime-only rate applied with no Prime input (E12)

**Problem.** ICICI Amazon Pay is valued at its Prime-member rate, and the tool has no input for Prime membership.

**Observed.**
- **Q01** row: `"net_annual_savings": "₹9,000"` on ₹15,000/month Amazon.
- **Card data:** "5% unlimited cashback on Amazon purchases for Prime members … 3% … for non-Prime members".

**Expected (reviewer arithmetic):** non-Prime gives 3% of ₹1,80,000 = ₹5,400.

**Possible solution:** add an optional `amazon_prime` boolean. If it's absent, return both values (or the lower one) with a `conditions` note. Apply the same pattern to any membership-dependent rate.

**Test:** `amazon_spends=15000, amazon_prime=false` → ICICI Amazon Pay ₹5,400; `true` → ₹9,000.

## B7. Transaction fees not deducted (E13)

**Problem.** Net savings subtract only the card fees, not per-transaction charges in `fee_schedule`. That makes "net" misleading for rent, and possibly for fuel and utilities.

**Observed.**
- **Q05** IDFC FIRST WOW Black: `"net_annual_savings": "₹4,800"`.
- **`get_card_details`:** `fee_schedule.rent_payment_fee: "1%"`.

**Expected (reviewer arithmetic):** about ₹3,600/yr in fees on ₹3,60,000 of rent.

**Possible solution:** subtract `fee_schedule` charges for rewarded categories, or return them as `category_fees` with a flag.

**Test:** `rent=30000` → the WOW Black net reflects the 1% fee, or the row carries a `category_fees` entry for rent.

**Open:** the ₹4,800 reward itself couldn't be checked, because no rent earn rate is in the returned terms.

## B8. `list_cards` ignores its filters

**Problem.** Every documented filter except `category` is ignored: `free_cards`, `annual_fees`, `bank_ids`, `credit_score`, `card_networks`. The description tells clients to map "lifetime free" to these filters.

**Observed** (`total_available` and the first rows are identical to the unfiltered call):

| Request | `total_available` |
|---|---|
| `{}` (unfiltered) | 258 |
| `{"free_cards": "true"}` | 258; first row SBI Cashback, annual fee ₹1,179 |
| `{"annual_fees": "free"}` | 258 |
| `{"annual_fees": "500-1000"}` | 258 |
| `{"bank_ids": [3]}` | 258; first rows SBI, Axis, HSBC |
| `{"credit_score": "650"}` | 258 |
| `{"card_networks": ["RuPay"]}` | 258 |
| `{"category": "best-travel-credit-card"}` | **183** (works) |

- **Cost to clients:** Q14 in the final run made 7 `list_cards` calls, up to `limit: 258`, to filter free cards by hand. That case alone cost $0.26 of LLM usage.

**Possible solution:**
- Implement the filters server-side, or remove them from the schema so clients don't rely on them.
- Return the applied filters in the response (`filters_applied`), so a client can tell when one was ignored.

**Test:**
- `{"free_cards": "true"}` → every row has `annual_fee` and `joining_fee` = "Free", and `total_available` < 258.
- `{"bank_ids": [3]}` → only SBI cards.
- `{"card_networks": ["RuPay"]}` → only RuPay cards.

## B9. Advisor playbook guidance conflicts with grounded answers (E14, E04)

**Problem.** `get_advisor_context`, which clients are told to load first, includes instructions that cause failures.
- **(a)** "MINIMUM REQUIRED: at least 2 spending categories with amounts before calling recommend_cards". The bot then refuses to rank single-category questions (Q02, Q05, Q06 T1).
- **(b)** "Your savings of ₹Y more than cover this in [Z] months". This asks the model to compute a payback figure no tool returns, and it caused the baseline's calculated ₹ figures (E04).

**Observed.** `discovery/raw/context__advisor_full.json`; Q06 T1's trace (only `get_advisor_context`, no ranking).

**Possible solution:**
- Change (a) to "rank with what the user gave, then ask for more categories to refine".
- Replace (b) with a returned field: `recommend_cards` returns `payback_months` (joining fee ÷ monthly net), so the figure comes from the tool.

**Test:** a client following the playbook on "I spend ₹15,000 a month on Amazon, best card?" calls `recommend_cards`. The playbook contains no instruction to compute a ₹ or months figure.

## B10. `check_eligibility` input handling (E15)

**Problem.** Bad inputs return a well-formed empty result instead of an error, and the count doesn't match the rows returned.

**Observed.**
- **Pincode `123456`** (Q16 T2) and **`000000`** → `"eligible_cards_count": 0`, `isError: false`.
- **`annual_income: "50k"`** → `"annual_income": "₹NaN"`, 0 cards, `isError: false`.
- **Row count:** `eligible_cards_count: 232` with 15 rows and no pagination parameter.

**Possible solution:**
- Validate the pincode against the serviceability table; return `isError: true`, "unknown pincode", when it isn't in it.
- Validate that income is digits only.
- Add `offset`/`limit`, or rename the count to `eligible_cards_total` and add `showing: 15`.

**Test:**
- `123456` and `000000` → error;
- `"50k"` → error;
- the response states how many rows it shows and how to get the rest.

## B11. Resolver reports high confidence for another bank's card

**Problem.** `whatsapp_resolve_card_or_category` matches a phrase naming one bank to a card from another bank, with `confidence: "high"`.

**Observed.** Q12: `{"phrase": "HDFC Platinum Ultra Max"}` → `"name": "RBL Platinum Maxima Credit Card", "confidence": "high"` (and RBL Platinum Maxima Plus, also "high"). The bot correctly refused it.

**Possible solution:**
- If the phrase names a bank and the match is from a different bank, cap the confidence at "low", or return no match.
- Return `matched_on` (name tokens vs bank) so clients can judge.

**Test:** `"HDFC Platinum Ultra Max"` → no RBL card at "high"; `"RBL Platinum Maxima"` → still "high".

## B12. Data quality and contract gaps (low harm, often seen)

| Problem | Observed | Possible solution |
|---|---|---|
| `bank` is `""` on every list, eligibility and resolver row | Q09, Q12, Q14–Q17; all discovery list rows | Fill it from `bank_id` (`get_card_details` has `"bank": "HDFC"`) |
| Structured `milestone_benefits` are null while the text describes a milestone | Landmark, Regalia Gold, Millenia: `[{"spend_target": null, "reward": null, "description": null}]` | Populate from the terms (also needed for B1) |
| Unrounded money strings | Q08: `"annual_rewards_value": "₹1,31,219.997"` | Round to whole rupees before formatting |
| Brief `list_cards` rows have no `card_type`/network | Q14: the bot couldn't confirm RuPay without a detail call per card | Include `card_network` in brief rows |
| `lounge_access` in `recommend_cards` reflects the user's usage, not the card's benefit | Q06: ixigo AU shows `domestic_per_quarter: 0` with no usage entered, though its terms give 8 visits/yr; the bot said "Lounge access: None" | Rename to `lounge_usage_valued`, and add `lounge_allowance` from the card terms |
| Income floors disagree within one card record | SBI Cashback 3 LPA vs `min_income_monthly` 30,000 (₹3.6 L/yr); Millenia 4 LPA vs 35,000 (₹4.2 L/yr) | Choose one authoritative field (see Part A §4.4) |

---

# Part C. Needs more investigation before a fix can be specified

| Item | Why it's open | What would settle it |
|---|---|---|
| `existing_customer_only: true` on SBI Cashback, HDFC Millenia, HSBC Live+ (Q02, Q03, Q20) | It contradicts `new_to_credit: true` on some of the same cards; the real-world rule isn't in the tool data | Issuer product pages / MITC; the data owner's definition of the flag |
| Scapia listed under `"bank": "Axis"` (Q09) | Only outside knowledge disputes it | Scapia's issuer from its official site or MITC |
| B1 mechanism (record vs formula) | ₹2.50/point matches no conversion in the data | The stored milestone record for `sbi-landmark-reward-select-credit-card`; the engine's milestone code |
| B2 location (engine vs data) | Identical output either way | The reward rule each card applies to `dining_or_going_out` |
| E01 mechanism (Part A §7) | Two explanations fit the observed calls | A code read, or two boundary calls (approval needed) |
| ICICI Emeralde in the ₹6 L self-employed list | Its income floor wasn't fetched | `get_card_details{"card_alias": "icici-emeralde-credit-card"}` (one call, approval needed) |
| B7 reward side | No rent earn rate in the returned terms | IDFC WOW Black MITC |

