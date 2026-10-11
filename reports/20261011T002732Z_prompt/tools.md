# Per-tool rollup

From the execution traces. Diagnosis questions per tool (D-codes) are in evals/CASES.md section 2.

| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |
|---|---|---|---|---|---|---|---|
| check_eligibility | 3 | 3 | — | 805 / 1031 | 7,301 | 0 | Q15, Q16 |
| compare_cards | 2 | 2 | — | 162 / 177 | 10,584 | 0 | Q13 |
| get_advisor_context | 19 | 19 | — | 713 / 898 | 38,558 | 0 | Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q10, Q11, Q12, Q13, Q14, Q15, Q16, Q17, Q18, Q19, Q20 |
| get_card_details | 10 | 8 | tool_error 2 | 189 / 689 | 5,992 | 0 | Q07, Q09, Q10, Q11, Q12, Q15, Q20 |
| list_cards | 5 | 5 | — | 525 / 611 | 16,989 | 0 | Q09, Q12, Q14, Q17 |
| recommend_cards | 14 | 14 | — | 4140 / 4707 | 19,440 | 0 | Q01, Q03, Q04, Q06, Q07, Q08, Q09, Q11, Q13, Q15, Q20 |
| whatsapp_resolve_card_or_category | 3 | 3 | — | 628 / 791 | 1,176 | 0 | Q12, Q13 |
