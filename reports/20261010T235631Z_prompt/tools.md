# Per-tool rollup

From the execution traces. Diagnosis questions per tool (D-codes) are in evals/CASES.md section 2.

| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |
|---|---|---|---|---|---|---|---|
| compare_cards | 2 | 2 | — | 166 / 188 | 10,584 | 0 | Q13 |
| get_advisor_context | 9 | 9 | — | 697 / 718 | 42,541 | 0 | Q01, Q03, Q05, Q07, Q09, Q10, Q11, Q13, Q20 |
| get_card_details | 5 | 5 | — | 135 / 147 | 7,530 | 0 | Q03, Q07, Q10, Q11, Q20 |
| list_cards | 1 | 1 | — | 489 / 489 | 6,119 | 0 | Q09 |
| recommend_cards | 6 | 6 | — | 4205 / 4771 | 11,330 | 0 | Q03, Q07, Q11, Q13, Q20 |
| whatsapp_resolve_card_or_category | 1 | 1 | — | 995 / 995 | 1,163 | 0 | Q13 |

**Core tools never called in this run:** check_eligibility
