"""Discovery scenarios, grouped by the question each group answers.

Each scenario changes one variable relative to a baseline so differences in the
output can be attributed to that variable.
"""

R = "recommend_cards"

SCENARIOS = {
    # What the server tells LLMs to do, and its own health view.
    "context": [
        {"id": "advisor_tool_guide", "tool": "get_advisor_context", "args": {}, "purpose": "default topic"},
        {"id": "advisor_full", "tool": "get_advisor_context", "args": {"topic": "full"}, "purpose": "full playbook, size"},
        {"id": "advisor_unit_conversion", "tool": "get_advisor_context", "args": {"topic": "unit_conversion"}, "purpose": "unit rules"},
        {"id": "diagnostics_full", "tool": "run_api_diagnostics", "args": {"scope": "full", "include_samples": True}, "purpose": "server self-check"},
    ],

    # Units, linearity, caps, savings formula, ranking.
    "recommend": [
        {"id": "amazon_5k", "tool": R, "args": {"amazon_spends": 5000, "top_n": 5}, "purpose": "linearity low"},
        {"id": "amazon_15k", "tool": R, "args": {"amazon_spends": 15000, "top_n": 5}, "purpose": "linearity baseline"},
        {"id": "amazon_50k", "tool": R, "args": {"amazon_spends": 50000, "top_n": 5}, "purpose": "linearity high / caps"},
        {"id": "amazon_15k_top1", "tool": R, "args": {"amazon_spends": 15000, "top_n": 1}, "purpose": "ranking stable vs top_n"},
        {"id": "amazon_15k_top10", "tool": R, "args": {"amazon_spends": 15000, "top_n": 10}, "purpose": "ranking stable vs top_n"},
        {"id": "amazon_15k_repeat", "tool": R, "args": {"amazon_spends": 15000, "top_n": 5}, "purpose": "determinism"},
        {"id": "amazon_15k_brief", "tool": R, "args": {"amazon_spends": 15000, "top_n": 5, "response_format": "brief"}, "purpose": "format consistency"},
        {"id": "amazon_15k_comparison", "tool": R, "args": {"amazon_spends": 15000, "top_n": 5, "response_format": "comparison"}, "purpose": "format consistency"},
        {"id": "fuel_5k", "tool": R, "args": {"fuel": 5000, "top_n": 5}, "purpose": "single category"},
        {"id": "dining_10k", "tool": R, "args": {"dining_or_going_out": 10000, "top_n": 5}, "purpose": "single category"},
        {"id": "mixed_everyday", "tool": R, "args": {"amazon_spends": 8000, "flipkart_spends": 4000, "online_food_ordering": 4000, "grocery_spends_online": 6000, "fuel": 3000, "mobile_phone_bills": 800, "electricity_bills": 2500, "top_n": 5}, "purpose": "realistic mix"},
        {"id": "flights_annual_120k", "tool": R, "args": {"flights_annual": 120000, "top_n": 5}, "purpose": "annual unit"},
        {"id": "flights_annual_10k", "tool": R, "args": {"flights_annual": 10000, "top_n": 5}, "purpose": "monthly value mis-sent as annual"},
        {"id": "traveller_no_lounge", "tool": R, "args": {"flights_annual": 300000, "hotels_annual": 150000, "dining_or_going_out": 15000, "top_n": 5}, "purpose": "lounge baseline"},
        {"id": "traveller_lounge_2dom", "tool": R, "args": {"flights_annual": 300000, "hotels_annual": 150000, "dining_or_going_out": 15000, "domestic_lounge_usage_quarterly": 2, "top_n": 5}, "purpose": "lounge value effect"},
        {"id": "traveller_lounge_2dom_2intl", "tool": R, "args": {"flights_annual": 300000, "hotels_annual": 150000, "dining_or_going_out": 15000, "domestic_lounge_usage_quarterly": 2, "international_lounge_usage_quarterly": 2, "top_n": 5}, "purpose": "intl lounge value"},
        {"id": "rent_30k", "tool": R, "args": {"rent": 30000, "top_n": 5}, "purpose": "rent fee handling"},
        {"id": "insurance_life", "tool": R, "args": {"life_insurance": 50000, "insurance_health_annual": 25000, "top_n": 5}, "purpose": "annual insurance keys"},
    ],

    # Missing data and errors.
    "edge": [
        {"id": "empty_profile", "tool": R, "args": {}, "purpose": "no spend"},
        {"id": "all_zero", "tool": R, "args": {"amazon_spends": 0, "fuel": 0}, "purpose": "zero spend"},
        {"id": "negative_spend", "tool": R, "args": {"amazon_spends": -5000}, "purpose": "invalid value"},
        {"id": "string_spend", "tool": R, "args": {"amazon_spends": "15k"}, "purpose": "wrong type"},
        {"id": "unknown_key", "tool": R, "args": {"netflix_spends": 1000, "amazon_spends": 5000}, "purpose": "unknown key silently dropped?"},
        {"id": "huge_spend", "tool": R, "args": {"amazon_spends": 10000000}, "purpose": "absurd value"},
        {"id": "details_bad_alias", "tool": "get_card_details", "args": {"card_alias": "hdfc-regalia"}, "purpose": "error format"},
        {"id": "details_typo_alias", "tool": "get_card_details", "args": {"card_alias": "icici-amazon-pay"}, "purpose": "near-miss alias"},
        {"id": "compare_one_card", "tool": "compare_cards", "args": {"card_aliases": ["icici-amazon-pay-credit-card"]}, "purpose": "below min"},
    ],

    # Card data for cards that appear in recommendations + listing.
    "cards": [
        {"id": "details_icici_amazon_pay", "tool": "get_card_details", "args": {"card_alias": "icici-amazon-pay-credit-card"}},
        {"id": "details_hdfc_millenia", "tool": "get_card_details", "args": {"card_alias": "hdfc-millenia-credit-card"}},
        {"id": "details_swiggy_hdfc", "tool": "get_card_details", "args": {"card_alias": "swiggy-ornge-hdfc-credit-card"}},
        {"id": "details_sbi_cashback", "tool": "get_card_details", "args": {"card_alias": "sbi-cashback-credit-card"}},
        {"id": "details_axis_flipkart", "tool": "get_card_details", "args": {"card_alias": "axis-flipkart-credit-card"}},
        {"id": "details_regalia_gold_a", "tool": "get_card_details", "args": {"card_alias": "hdfc-regalia-gold"}, "purpose": "alias from description list"},
        {"id": "details_regalia_gold_b", "tool": "get_card_details", "args": {"card_alias": "hdfc-regalia-gold-credit-card"}, "purpose": "alias from description example"},
        {"id": "details_magnus_a", "tool": "get_card_details", "args": {"card_alias": "axis-bank-magnus-credit-card"}},
        {"id": "details_magnus_b", "tool": "get_card_details", "args": {"card_alias": "axis-magnus-credit-card"}},
        {"id": "details_whatsapp_icici_amazon", "tool": "whatsapp_get_card_details", "args": {"card_alias": "icici-amazon-pay-credit-card"}, "purpose": "facade consistency"},
        {"id": "list_default", "tool": "list_cards", "args": {}},
        {"id": "list_all_brief_200", "tool": "list_cards", "args": {"limit": 250, "response_format": "brief"}, "purpose": "alias inventory"},
        {"id": "list_free", "tool": "list_cards", "args": {"free_cards": "true", "limit": 20, "response_format": "brief"}},
        {"id": "list_fee_free", "tool": "list_cards", "args": {"annual_fees": "free", "limit": 20, "response_format": "brief"}, "purpose": "two ways to say free agree?"},
        {"id": "list_travel", "tool": "list_cards", "args": {"category": "best-travel-credit-card", "limit": 10}},
    ],

    # Loose card names.
    "resolve": [
        {"id": "resolve_regalia", "tool": "whatsapp_resolve_card_or_category", "args": {"phrase": "regalia"}},
        {"id": "resolve_hdfc_regalia_gold", "tool": "whatsapp_resolve_card_or_category", "args": {"phrase": "hdfc regalia gold"}},
        {"id": "resolve_amazon_card", "tool": "whatsapp_resolve_card_or_category", "args": {"phrase": "amazon card"}},
        {"id": "resolve_magnus", "tool": "whatsapp_resolve_card_or_category", "args": {"phrase": "magnus"}},
        {"id": "resolve_sbi_cashbak_typo", "tool": "whatsapp_resolve_card_or_category", "args": {"phrase": "sbi cashbak"}},
        {"id": "resolve_millenia_typo", "tool": "whatsapp_resolve_card_or_category", "args": {"phrase": "hdfc millennia"}},
    ],

    # Cross-tool consistency for the same input.
    "consistency": [
        {"id": "wa_profile_amazon_15k", "tool": "whatsapp_recommend_cards_for_spend_profile", "args": {"spend_profile": {"amazon_spends": 15000}, "top_n": 5}},
        {"id": "wa_category_shopping_15k", "tool": "whatsapp_recommend_cards_for_category_spend", "args": {"category": "shopping", "amount": 15000}},
        {"id": "wa_profile_mixed", "tool": "whatsapp_recommend_cards_for_spend_profile", "args": {"spend_profile": {"amazon_spends": 8000, "flipkart_spends": 4000, "online_food_ordering": 4000, "grocery_spends_online": 6000, "fuel": 3000, "mobile_phone_bills": 800, "electricity_bills": 2500}, "top_n": 5}},
        {"id": "wa_category_fuel_5k", "tool": "whatsapp_recommend_cards_for_category_spend", "args": {"category": "fuel", "amount": 5000}},
        {"id": "wa_category_travel_default", "tool": "whatsapp_recommend_cards_for_category_spend", "args": {"category": "travel", "amount": 120000}, "purpose": "travel defaults annual?"},
        {"id": "compare_amazon_vs_sbi", "tool": "compare_cards", "args": {"card_aliases": ["icici-amazon-pay-credit-card", "sbi-cashback-credit-card"]}},
        {"id": "wa_compare_amazon_vs_sbi", "tool": "whatsapp_compare_cards", "args": {"card_aliases": ["icici-amazon-pay-credit-card", "sbi-cashback-credit-card"]}},
        {"id": "wa_compare_amazon_vs_sbi_spend", "tool": "whatsapp_compare_cards", "args": {"card_aliases": ["icici-amazon-pay-credit-card", "sbi-cashback-credit-card"], "spend_profile": {"amazon_spends": 15000}}},
    ],

    # Eligibility semantics.
    "eligibility": [
        {"id": "mumbai_6L_salaried", "tool": "check_eligibility", "args": {"pincode": "400001", "annual_income": "600000", "employment_status": "salaried"}},
        {"id": "mumbai_6L_self", "tool": "check_eligibility", "args": {"pincode": "400001", "annual_income": "600000", "employment_status": "self_employed"}},
        {"id": "mumbai_25L_salaried", "tool": "check_eligibility", "args": {"pincode": "400001", "annual_income": "2500000", "employment_status": "salaried"}},
        {"id": "rural_3L_salaried", "tool": "check_eligibility", "args": {"pincode": "848101", "annual_income": "300000", "employment_status": "salaried"}},
        {"id": "invalid_pincode", "tool": "check_eligibility", "args": {"pincode": "000000", "annual_income": "600000", "employment_status": "salaried"}},
        {"id": "income_50k_string", "tool": "check_eligibility", "args": {"pincode": "400001", "annual_income": "50k", "employment_status": "salaried"}},
    ],
}

# Follow-ups from the first pass: rate-limited retries, cap behaviour, milestone-heavy cards.
SCENARIOS["followup"] = [
    {"id": "elig_rural_3L_salaried", "tool": "check_eligibility", "args": {"pincode": "848101", "annual_income": "300000", "employment_status": "salaried"}, "purpose": "retry after 429"},
    {"id": "elig_invalid_pincode", "tool": "check_eligibility", "args": {"pincode": "000000", "annual_income": "600000", "employment_status": "salaried"}, "purpose": "retry after 429"},
    {"id": "elig_income_50k_string", "tool": "check_eligibility", "args": {"pincode": "400001", "annual_income": "50k", "employment_status": "salaried"}, "purpose": "retry after 429"},
    {"id": "elig_mumbai_1L_salaried", "tool": "check_eligibility", "args": {"pincode": "400001", "annual_income": "100000", "employment_status": "salaried"}, "purpose": "does income filter anything?"},
    {"id": "amazon_50k_top25", "tool": R, "args": {"amazon_spends": 50000, "top_n": 25}, "purpose": "caps: SBI Cashback ₹2k/cycle, Swiggy ₹1.5k/cycle, Millenia"},
    {"id": "details_sbi_landmark_select", "tool": "get_card_details", "args": {"card_alias": "sbi-landmark-reward-select-credit-card"}, "purpose": "₹30k milestone source"},
    {"id": "details_ixigo_au", "tool": "get_card_details", "args": {"card_alias": "ixigo-au-credit-card"}, "purpose": "₹20k milestone source"},
    {"id": "details_bob_cashback", "tool": "get_card_details", "args": {"card_alias": "bob-cashback-credit-card"}, "purpose": "5% on Amazon/dining source"},
    {"id": "details_amex_gold", "tool": "get_card_details", "args": {"card_alias": "american-express-gold-card"}, "purpose": "milestone vs hidden in facade"},
]

# Probe set 2: ground truth for edge cases in evals/CASES.md v2 (filters/limits never observed before)
SCENARIOS["p2"] = [
    {"id": "list_rupay", "tool": "list_cards", "args": {"card_networks": ["RuPay"], "limit": 10},
     "purpose": "network filter: are all rows RuPay? (UPI-on-credit-card question)"},
    {"id": "list_bank_sbi", "tool": "list_cards", "args": {"bank_ids": [3], "limit": 10, "response_format": "brief"},
     "purpose": "bank filter with SBI bank_id=3 (from get_card_details); bank field is empty in rows"},
    {"id": "list_credit_650", "tool": "list_cards", "args": {"credit_score": "650", "limit": 10, "response_format": "brief"},
     "purpose": "credit_score filter semantics (undocumented format)"},
    {"id": "list_fee_500_1000", "tool": "list_cards", "args": {"annual_fees": "500-1000", "limit": 10, "response_format": "brief"},
     "purpose": "fee range filter: are all annual fees within 500-1000?"},
    {"id": "compare_bad_plus_good", "tool": "compare_cards", "args": {"card_aliases": ["axis-magnus-credit-card", "sbi-cashback-credit-card"]},
     "purpose": "one broken (description-example) alias + one valid: whole-call error or partial?"},
    {"id": "recommend_amz15_dining5_top50", "tool": "recommend_cards",
     "args": {"amazon_spends": 15000, "dining_or_going_out": 5000, "top_n": 50, "response_format": "brief"},
     "purpose": "oracle nets for a spend-aware 4-card comparison (Magnus, Amazon Pay, SBI Cashback, Millenia)"},
    {"id": "elig_123456_self_6L", "tool": "check_eligibility",
     "args": {"pincode": "123456", "annual_income": "600000", "employment_status": "self_employed"},
     "purpose": "placeholder-style 6-digit pincode: silent 0 or error?"},
    {"id": "elig_delhi_self_6L", "tool": "check_eligibility",
     "args": {"pincode": "110001", "annual_income": "600000", "employment_status": "self_employed"},
     "purpose": "baseline for the self-employed 50k/month case"},
    {"id": "elig_delhi_income_0", "tool": "check_eligibility",
     "args": {"pincode": "110001", "annual_income": "0", "employment_status": "salaried"},
     "purpose": "student / no income: what does income 0 return?"},
    {"id": "details_idfc_wow_black", "tool": "get_card_details", "args": {"card_alias": "idfc-first-wow-black-credit-card"},
     "purpose": "#1 card for rent: rent fee / exclusions vs recommend_cards crediting rent rewards"},
]
