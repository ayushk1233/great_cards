# Per-tool rollup

From the execution traces. Diagnosis questions per tool (D-codes) are in evals/CASES.md section 2.

| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |
|---|---|---|---|---|---|---|---|
| check_eligibility | 3 | 3 | — | 906 / 1109 | 7,301 | 0 | Q15, Q16 |
| compare_cards | 2 | 2 | — | 146 / 147 | 7,882 | 0 | Q11, Q13 |
| get_advisor_context | 20 | 20 | — | 684 / 927 | 34,815 | 0 | Q01, Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20 |
| get_card_details | 13 | 11 | tool_error 2 | 137 / 153 | 6,440 | 0 | Q02, Q03, Q05, Q07, Q09, Q10, Q11, Q12, Q20 |
| list_cards | 4 | 4 | — | 490 / 537 | 16,223 | 0 | Q09, Q14, Q17 |
| recommend_cards | 15 | 15 | — | 4109 / 4564 | 7,656 | 0 | Q01, Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q11, Q13, Q15, Q20 |
| whatsapp_resolve_card_or_category | 3 | 3 | — | 542 / 570 | 571 | 0 | Q12 |
