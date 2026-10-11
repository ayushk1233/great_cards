# Per-tool rollup

From the execution traces. Diagnosis questions per tool (D-codes) are in evals/CASES.md section 2.

| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |
|---|---|---|---|---|---|---|---|
| get_advisor_context | 2 | 2 | — | 695 / 696 | 42,541 | 0 | Q07, Q09 |
| get_card_details | 4 | 4 | — | 129 / 139 | 6,961 | 0 | Q07, Q09 |
| list_cards | 1 | 1 | — | 488 / 488 | 7,640 | 0 | Q09 |
| recommend_cards | 2 | 2 | — | 4214 / 4384 | 7,615 | 0 | Q07, Q09 |

**Core tools never called in this run:** compare_cards, check_eligibility
