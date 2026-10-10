# MCP Discovery Findings — Great.cards server

Server `https://bk-api.bankkaro.com/mcp`, `great-cards` v1.6.1. Probed 2026-10-10/11 with the official MCP Python SDK ([probe.py](probe.py), scenarios in [scenarios.py](scenarios.py)). 75 logged tool calls ([call_log.jsonl](call_log.jsonl)), run sequentially.

**Tags:** **VERIFIED** = seen directly in raw output (file linked) · **ASSUMPTION** = inference that fits the evidence but isn't proven · **UNKNOWN** = can't be determined from what the server returns.

Raw evidence lives in `raw/<group>__<id>.json`. Each file holds the exact request, the raw MCP result, the parsed JSON and the latency.

---

## 1. Transport and session

| Observation | Tag | Evidence |
|---|---|---|
| Streamable HTTP: POST JSON-RPC to `/mcp`; responses come as `text/event-stream` with one `message` event | VERIFIED | curl probe; SDK connects cleanly |
| `initialize` returns an `mcp-session-id` header. The SDK negotiates protocol `2025-11-25`, and a raw probe offering `2025-06-18` was accepted | VERIFIED | [server_info.json](server_info.json) |
| Capabilities: `tools` and `prompts` (both `listChanged`); no resources | VERIFIED | server_info.json |
| **Rate limiting:** HTTP 429 after ~65 calls in ~3 min; session DELETE also got 429. It recovered after a short wait | VERIFIED | first-run eligibility rows in call_log.jsonl (`client_error`) |
| Rate-limit thresholds and window | UNKNOWN | — |
| Latency: `recommend_cards` ~3.1–4.6 s; whatsapp recommend ~1.6–1.8 s; details/compare ~0.1–0.2 s; eligibility ~0.3–1.4 s; `run_api_diagnostics` 3.7 s | VERIFIED | call_log.jsonl |

## 2. Tool inventory

| Observation | Tag | Evidence |
|---|---|---|
| **14 tools**, not the 5 in the brief: 6 core (`get_advisor_context`, `recommend_cards`, `get_card_details`, `list_cards`, `compare_cards`, `check_eligibility`), 6 `whatsapp_*` facades, `generate_content_brief`, `run_api_diagnostics` | VERIFIED | [tool_catalog.md](tool_catalog.md) |
| 1 prompt, `card-advisor` (~40k chars of system instructions) | VERIFIED | [prompts.json](prompts.json) |
| No tool declares `outputSchema` or `annotations`. Results arrive as a JSON string in `content[0].text`, with no `structuredContent` | VERIFIED | tools.json, any raw file |
| `get_advisor_context(full)` is ~42k chars (server estimate ~13k tokens) and is meant to be injected into the system prompt | VERIFIED | raw/context__advisor_full.json |

## 3. Input units (`recommend_cards`)

| Observation | Tag | Evidence |
|---|---|---|
| Most spend keys are **monthly ₹**; `flights_annual`, `hotels_annual`, `insurance_health_annual`, `insurance_car_or_bike_annual` and `life_insurance` are **annual**; lounge keys are **visits per quarter** | VERIFIED (descriptions) | tool_catalog.md |
| The server trusts whatever number it gets. `flights_annual: 10000` is treated as ₹10k a year (→ ₹500 at 5%), so a monthly figure passed by mistake silently understates value 12× | VERIFIED | recommend__flights_annual_10k |
| No field is required. `{}`, all-zero and **negative** values return a ranked list of ₹0 cards with no warning | VERIFIED | edge__empty_profile, edge__all_zero, edge__negative_spend |
| Wrong type (`"15k"`) → `isError: true`, `-32602` validation error | VERIFIED | edge__string_spend |
| **Unknown keys are silently dropped** (`netflix_spends` ignored, no error) | VERIFIED | edge__unknown_key |
| No upper-bound check: ₹1 crore/month on Amazon → ₹1.87 crore of "savings" | VERIFIED | edge__huge_spend |

## 4. Output fields (`recommend_cards`, `response_format=full`)

| Observation | Tag | Evidence |
|---|---|---|
| Per card: `rank, card_name, bank_name, card_type, net_annual_savings, annual_rewards_value, milestone_benefits, lounge_value, joining_fee, annual_fee, annual_fee_waived, welcome_benefits[], voucher, lounge_access{}, top_spend_categories[], card_alias, rating, image` plus top-level `total_cards_analyzed` and `_format_hint` | VERIFIED | recommend__amazon_15k |
| Money is **formatted strings** in `full`/`brief` (`"₹9,000"`, `"₹1,180 (incl. GST)"`) and **plain numbers** in `comparison` | VERIFIED | recommend__amazon_15k_brief / _comparison |
| Float noise leaks into the strings: `"₹1,31,219.997"`, `"₹500.4"`, `"₹166.667"` | VERIFIED | recommend__traveller_*, recommend__flights_annual_10k, recommend__amazon_5k |
| **`top_spend_categories[].annual_value` is actually a *monthly* value.** For ₹15k/month Amazon at 5% it shows ₹750 (= 15,000 × 5%), while `annual_rewards_value` is ₹9,000 (= ₹750 × 12). This holds for every scenario | VERIFIED | recommend__amazon_5k / _15k / _50k |
| An internal key, `new_monthly_cat_1`, leaks into `top_spend_categories` | VERIFIED | recommend__amazon_15k (Swiggy Ornge row) |
| `bank` is empty (`""`) on all 250 `list_cards` rows and in eligibility and resolve results | VERIFIED | cards__list_all_brief_200 |
| `card_network` is always `null`; the network is in `card_type` | VERIFIED | any cards__details_* |
| `total_cards_analyzed` is 204, but `list_cards` reports `total_available` 258, and descriptions say "100+" | VERIFIED | recommend__*, cards__list_default |

## 5. Savings definition and ranking

| Observation | Tag | Evidence |
|---|---|---|
| **Observed formula:** `net = annual_rewards + milestone + lounge − annual_fee`, where annual_fee = 0 when the spend waiver is met. It matches all checked rows: BOB 9,000 − 589 = 8,411; AMEX Gold 6,960 + 6,960 − 5,310 = 8,610; IDFC Mayura 3,996,000 + 11,250 − 7,079 = 4,000,171 | VERIFIED | recommend__amazon_15k, _flights_annual_120k, edge__huge_spend |
| **The joining fee is never subtracted.** The `recommend_cards` description says "rewards + lounge + milestone − **joining fee** − annual fee". The response `_format_hint` leaves the joining fee out. HDFC Millenia (₹1,180 joining fee) shows net ₹9,000 = rewards ₹9,000 | VERIFIED (description vs behaviour conflict) | tool_catalog.md vs recommend__amazon_15k |
| Fee-waiver thresholds are applied against annualised spend (Millenia ₹1L: waived at ₹1.8L/yr; Swiggy ₹1.5L: not waived at ₹60k/yr) | VERIFIED | recommend__amazon_15k, _amazon_5k |
| Ranking is by `net_annual_savings`, descending. It's deterministic (repeat identical) and stable across `top_n` 1/5/10 | VERIFIED | recommend__amazon_15k_repeat / _top1 / _top10 |
| Tie-break between equal nets (3 cards at ₹9,000) | UNKNOWN (not rating: 3 → 5 → 3.1) | recommend__amazon_15k |
| Ranking ignores eligibility; recommendations don't know the user's income | VERIFIED (no income input exists) | tool_catalog.md |
| **Caps are applied** at ₹50k/month Amazon: SBI Cashback ₹2,000/month, Swiggy Ornge ₹1,500, BOB ₹1,500, Millenia ₹1,000. These match each card's own data | VERIFIED | followup__amazon_50k_top25 vs cards__details_* |
| Assumes Amazon **Prime** (5%) for ICICI Amazon Pay; the card data says non-Prime earns 3%. No input for Prime status | VERIFIED | recommend__amazon_15k vs cards__details_icici_amazon_pay |
| **Per-transaction fees are ignored:** for ₹30k/month rent, #1 IDFC FIRST WOW! Black shows net ₹4,800 = rewards, but its `fee_schedule.rent_payment_fee` is 1%. Rent isn't in its exclusions | VERIFIED | recommend__rent_30k vs p2__details_idfc_wow_black |
| Fee waiver flag is correct at the threshold: ₹15k Amazon + ₹2k food (₹2.04L/yr) → SBI Cashback `annual_fee_waived: true` (waiver ₹2L) | VERIFIED | p2__s01_recommend_amz15_food2 |
| **3-way tie at the top for ₹15k Amazon** (Millenia, ICICI Amazon Pay, Swiggy Ornge, all ₹9,000). Millenia ranks #1 despite a ₹1,180 joining fee vs ICICI's ₹0, a direct effect of the joining fee being excluded (C5) | VERIFIED | recommend__amazon_15k |

## 6. Lounge valuation

| Observation | Tag | Evidence |
|---|---|---|
| **Lounge value is counted for one quarter, then added to an *annual* total.** 2 domestic visits per quarter → `lounge_value` ₹1,500 (= 2 × ₹750). A year is 8 visits = ₹6,000. Adding 2 international per quarter → +₹2,500 (= 2 × ₹1,250), not ₹10,000 | VERIFIED | recommend__traveller_lounge_2dom vs _no_lounge vs _2dom_2intl |
| `lounge_access.*_per_quarter` holds the card's allowance. ixigo AU shows domestic 8/quarter and international 1/quarter, but its own data says "8 domestic … a year and 1 international" | VERIFIED (mismatch) | recommend__traveller_lounge_2dom_2intl vs followup__details_ixigo_au |

## 7. Category → reward-rate mapping (conflicts with card data)

| Observation | Tag | Evidence |
|---|---|---|
| ICICI Amazon Pay earns **5% on `flights_annual`** (₹6,000 on ₹1.2L). Its own data says "1% on all other spends" and "Flight Benefits: none" | VERIFIED (conflict) | recommend__flights_annual_120k vs cards__details_icici_amazon_pay |
| BOB Cashback, CRED IndusInd and SBI Cashback earn **5% on in-person dining** (₹6,000 on ₹10k/month). BOB's data says 5% only on "domestic online spends"; SBI's says 5% only on dining "processed through online platforms". The key description defines `dining_or_going_out` as IN-PERSON | VERIFIED (conflict) | recommend__dining_10k vs followup__details_bob_cashback, cards__details_sbi_cashback |
| Root cause (engine maps dining/flights to an "online" bucket, or the card data rules are mis-tagged) | ASSUMPTION | — |

## 8. Milestone valuation

| Observation | Tag | Evidence |
|---|---|---|
| **SBI Landmark Reward SELECT: milestone ₹30,000.** The card's data says 12,000 bonus RP on ₹3L a year, with `point_value` "1 RP = ₹0.25", which is **₹3,000**. That makes it 10× high, and it ranks **#1** for an everyday mixed profile | VERIFIED (conflict) | recommend__mixed_everyday vs followup__details_sbi_landmark_select |
| **ixigo AU: milestone ₹20,000.** The data says 5,000 RP per quarter on ₹75k, which is 20,000 RP a year, at "1 RP = ₹0.20", so **₹4,000**. It matches RP valued at ₹1 | VERIFIED (conflict) | recommend__mixed_everyday vs followup__details_ixigo_au |
| HDFC Millenia: milestone ₹4,000 at ₹1.5L per quarter (₹1,000 voucher × 4 quarters) is consistent with its data | VERIFIED | followup__amazon_50k_top25 |
| The structured `milestone_benefits` field in `get_card_details` is null-filled (`[{spend_target:null,…}]`) for Millenia, Regalia Gold, Landmark and AMEX Gold; milestones exist only as free text | VERIFIED | cards__details_* |
| The whatsapp facade drops the milestone component: AMEX Gold `annual_value` ₹8,749 > `annual_rewards` ₹7,099 despite a ₹5,310 fee, with no explanation | VERIFIED | consistency__wa_category_shopping_15k |

## 9. Card details and alias resolution

| Observation | Tag | Evidence |
|---|---|---|
| `get_card_details` returns: name, bank, fees{joining, annual, waiver, gst_note}, fee_schedule{APR, forex, late slabs, tnc_url}, rewards{point_value, exclusions}, key_benefits, detailed_benefits, eligibility{age, income LPA, CRIF}, flags | VERIFIED | cards__details_icici_amazon_pay |
| **Unknown alias → `{"error": "Card not found: …"}` with `isError` absent.** To an LLM it looks like a successful call | VERIFIED | edge__details_bad_alias |
| **Example aliases in the tool descriptions don't work.** `get_card_details`' own parameter example `hdfc-regalia-gold-credit-card` and `compare_cards`' example `axis-magnus-credit-card` both return "Card not found". Working: `hdfc-regalia-gold`, `axis-bank-magnus-credit-card` | VERIFIED | cards__details_regalia_gold_b, cards__details_magnus_b |
| `whatsapp_resolve_card_or_category` handles "regalia", "magnus" (returns 2 options) and "hdfc millennia" (typo), but **fails on "sbi cashbak"** (0 matches) | VERIFIED | resolve__* |
| `existing_customer_only: true` on ICICI Amazon Pay, Millenia, Swiggy Ornge, SBI Cashback and Axis Flipkart, often alongside `new_to_credit: true` (contradictory) | VERIFIED (internal contradiction); real-world truth UNKNOWN | cards__details_* |
| The whatsapp details facade has garbled `top_benefits` (description fragments without titles, repeated 3×) | VERIFIED | cards__details_whatsapp_icici_amazon |
| Core `compare_cards` returns two full detail blobs with no numbers and no winner; `whatsapp_compare_cards` with spend gives a winner and values matching `recommend_cards` | VERIFIED | consistency__compare_*, consistency__wa_compare_* |
| **One bad alias fails the whole comparison:** `["axis-magnus-credit-card" (the description's own example), "sbi-cashback-credit-card"]` returns `{"error": "Could not fetch enough cards for comparison. Check the aliases provided."}` with no `isError` and without naming the bad alias | VERIFIED | p2__compare_bad_plus_good |
| Spend-aware comparison of an arbitrary card isn't possible with the 6 core tools: core compare has no spend input, and Axis Magnus isn't in `recommend_cards` top 50 for ₹15k Amazon + ₹5k dining | VERIFIED | p2__recommend_amz15_dining5_top50 |

## 10. `list_cards` filters

| Observation | Tag | Evidence |
|---|---|---|
| **`free_cards: "true"` and `annual_fees: "free"` are ignored:** 17 of 20 results have a paid annual fee, in the same order as the unfiltered list | VERIFIED | cards__list_free, cards__list_fee_free, cards__list_default |
| **Every other filter is ignored too.** `card_networks: ["RuPay"]` returns VISA/Mastercard rows. `bank_ids: [3]` (SBI's id from get_card_details) returns HDFC/Axis/HSBC rows. `credit_score: "650"` and `annual_fees: "500-1000"` (which includes a ₹2,950 card) return the **identical default list and order**, with `total_available` 258 each time | VERIFIED | p2__list_rupay, p2__list_bank_sbi, p2__list_credit_650, p2__list_fee_500_1000 vs cards__list_default |
| `category` does filter (the travel list differs from the default). It's the only filter seen working | VERIFIED | cards__list_travel |
| The network is only in `card_type` (e.g. "VISA,RuPay"); `card_network` is null and `bank` is empty, so the bot can't filter rows itself by network or bank reliably | VERIFIED | p2__list_rupay |

## 11. Eligibility (`check_eligibility`)

| Observation | Tag | Evidence |
|---|---|---|
| Returns `eligible_cards_count`, `profile` and **15** card rows (no pagination parameter). There's no approval language and no reasons | VERIFIED | eligibility__mumbai_6L_salaried |
| **Income barely filters:** ₹6L and ₹25L salaried give identical results (232). ₹1L → 201; rural pincode ₹3L → 200 | VERIFIED | eligibility__*, followup__elig_* |
| **HDFC Regalia Gold shows as eligible at ₹3L and ₹6L**, though its own data says `income_salaried_lpa: 18` | VERIFIED (conflict) | eligibility__mumbai_6L_salaried vs cards__details_regalia_gold_a |
| Employment filter works (the self-employed list drops salaried-only cards, e.g. HSBC Cashback) | VERIFIED | eligibility__mumbai_6L_self |
| Invalid pincode `000000` → count 0, no error. Income `"50k"` → profile shows `"₹NaN"`, count 0, no error | VERIFIED | followup__elig_invalid_pincode, followup__elig_income_50k_string |
| A placeholder-style pincode users really type, `123456`, also gives **0 cards with no error**. A 5-digit pincode is rejected by the schema (`minLength: 6`), so the silent zero only affects 6-digit codes | VERIFIED | p2__elig_123456_self_6L; tools.json |
| Self-employed ₹6L in Delhi → 231 eligible, 15 rows, and **Regalia Gold listed again** (its data says self-employed 18 LPA) | VERIFIED | p2__elig_delhi_self_6L |
| Income `"0"` → 3 cards (SBM Kredit.Pe, SBM ZET, IDFC FIRST WOW). Whether they're secured cards isn't verified. There's no age or student input | VERIFIED (count); ASSUMPTION (secured) | p2__elig_delhi_income_0 |
| "In-hand" vs gross income meaning, and whether CIBIL/age are checked | UNKNOWN (no input for either) | tool_catalog.md |

## 12. Server guidance that clashes with the assignment's guardrails

| Observation | Tag | Evidence |
|---|---|---|
| The playbook tells the LLM to say "Your savings of ₹Y more than cover this in [Z] months". That's a computed figure the tools don't return, which clashes with the rule against showing ₹ figures the tools didn't return | VERIFIED | raw/context__advisor_full.json |
| The whatsapp category tool silently splits ₹15k "shopping" into Amazon 6,000 / Flipkart 4,500 / other 4,500 | VERIFIED | consistency__wa_category_shopping_15k |

---

## Candidate failures (seed for Task 3)

| # | Issue | Likely bucket | Severity |
|---|---|---|---|
| C1 | Milestone overvaluation (Landmark 10×, ixigo 5×) pushes wrong cards to #1 | MCP (calc) / Data | **High** |
| C2 | Lounge value counted for one quarter but added to an annual total (4× under) | MCP (calc) | High |
| C3 | Eligibility income filter ineffective; Regalia Gold "eligible" at ₹3–6L | MCP / Data | High |
| C4 | 5% applied to in-person dining and flights against card terms | MCP mapping / Data | High |
| C5 | Joining fee excluded, contradicting the description | MCP (description) | Medium |
| C6 | `annual_value` field is monthly | MCP (labelling) | Medium (LLM will misquote) |
| C7 | Description example aliases fail; `error` returned without `isError` | MCP (description) | Medium |
| C8 | `list_cards` ignores every filter except `category` (free, fee range, network, bank, credit score) | MCP | **High** (browse answers are wrong whenever a filter is the point) |
| C9 | Silent acceptance of negative, unknown and garbage input (NaN) | MCP (validation) | Medium |
| C10 | Prime assumption undisclosed (ICICI Amazon Pay 5% vs 3%) | MCP / Model must disclose | Medium |
| C11 | Null structured milestones, empty `bank`, `existing_customer_only` contradictions | Data | Low–Med |
| C12 | Playbook instructs the model to produce un-returned ₹ figures | MCP (guidance) → Model guardrail | Medium |
| C13 | Rent rewards credited, but the card's own rent payment fee is ignored. IDFC FIRST WOW! Black is #1 for ₹30k/month rent at ₹4,800 net = rewards, while its `fee_schedule.rent_payment_fee` is 1% | MCP (calc ignores fee_schedule) | Medium–High |
| C14 | One bad alias fails the whole `compare_cards` call with a generic error and no `isError`; core compare can't do spend-aware comparison | MCP | Medium |
| C15 | Playbook "MINIMUM REQUIRED: at least 2 spending categories before calling recommend_cards" blocks single-category questions; playbook has no approval or tax guidance | MCP (guidance) → Model | Medium |

---

## Discovery checklist: evidence required before designing the chatbot

- [x] Verbatim tool and prompt catalog saved ([tool_catalog.md](tool_catalog.md), [tools.json](tools.json), [prompts.json](prompts.json))
- [x] Exact unit per spend key, confirmed by behaviour (annual and quarterly keys trusted as given)
- [x] Savings formula confirmed with ≥3 worked examples (joining fee excluded)
- [x] Ranking key confirmed; tie-break UNKNOWN
- [x] Money output format known (strings vs numbers by `response_format`), which feeds the ₹ guardrail
- [x] Error shapes: validation → `isError`; not-found → `{"error"}` with no `isError`; bad eligibility input → silent 0
- [x] Alias path: `whatsapp_resolve_card_or_category` → alias → `get_card_details` (with a `list_cards` fallback)
- [x] Eligibility semantics: a coarse filter, 15 rows, no approval language
- [x] Advisor context size (~42k chars) known
- [x] Latency per tool known (recommend ~3–4 s), which matters for UI loading states
- [x] Rate limit exists, so the bot must avoid redundant calls
- [ ] **Decision (yours):** which tool set the bot exposes to Haiku: core only, core + resolve, or the whatsapp facades
- [ ] **Decision (yours):** whether to inject `get_advisor_context(full)`, the `card-advisor` prompt, or our own shorter prompt (cost/latency vs. fidelity)
- [ ] **Hand verification (step 8 of the plan, not done yet):** check C1, C3 and C4 against official bank pages (SBI Landmark, ixigo AU, BOB Cashback, HDFC Regalia Gold) to separate MCP from Data
