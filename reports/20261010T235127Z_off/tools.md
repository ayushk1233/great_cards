# Per-tool rollup

From the execution traces. Diagnosis questions per tool (D-codes) are in evals/CASES.md section 2.

| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |
|---|---|---|---|---|---|---|---|
| compare_cards | 3 | 3 | — | 328 / 691 | 9,751 | 0 | Q11, Q13 |
| get_advisor_context | 9 | 9 | — | 701 / 737 | 42,541 | 0 | Q01, Q03, Q05, Q07, Q09, Q10, Q11, Q13, Q20 |
| get_card_details | 9 | 9 | — | 143 / 174 | 7,816 | 0 | Q03, Q07, Q09, Q10, Q11, Q20 |
| list_cards | 1 | 1 | — | 580 / 580 | 7,640 | 0 | Q09 |
| recommend_cards | 6 | 6 | — | 4139 / 4431 | 6,237 | 0 | Q03, Q07, Q09, Q11, Q13, Q20 |

**Core tools never called in this run:** check_eligibility
