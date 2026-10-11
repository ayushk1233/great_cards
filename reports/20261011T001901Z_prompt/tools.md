# Per-tool rollup

From the execution traces. Diagnosis questions per tool (D-codes) are in evals/CASES.md section 2.

| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |
|---|---|---|---|---|---|---|---|
| get_advisor_context | 3 | 3 | — | 698 / 712 | 29,660 | 0 | Q03, Q07, Q09 |
| get_card_details | 6 | 6 | — | 225 / 699 | 7,287 | 0 | Q07, Q09, Q20 |
| list_cards | 1 | 1 | — | 553 / 553 | 7,640 | 0 | Q09 |
| recommend_cards | 4 | 4 | — | 4115 / 4398 | 17,261 | 0 | Q03, Q07, Q09, Q20 |

**Core tools never called in this run:** compare_cards, check_eligibility
