# Per-tool rollup

From the execution traces. Diagnosis questions per tool (D-codes) are in evals/CASES.md section 2.

| tool | calls | ok | errors by kind | latency avg / max ms | payload avg chars | unknown-key calls | cases |
|---|---|---|---|---|---|---|---|
| check_eligibility | 3 | 3 | — | 842 / 1022 | 7,301 | 0 | Q15, Q16 |
| compare_cards | 1 | 1 | — | 157 / 157 | 7,680 | 0 | Q13 |
| get_advisor_context | 17 | 17 | — | 670 / 803 | 35,786 | 0 | Q01, Q02, Q03, Q04, Q05, Q06, Q07, Q08, Q09, Q10, Q11, Q12, Q13, Q14, Q15, Q17, Q19 |
| get_card_details | 14 | 11 | tool_error 3 | 198 / 745 | 5,737 | 0 | Q07, Q09, Q10, Q11, Q12, Q14, Q15, Q17, Q20 |
| list_cards | 10 | 10 | — | 534 / 799 | 20,220 | 0 | Q09, Q12, Q14, Q17 |
| recommend_cards | 14 | 14 | — | 4214 / 4627 | 10,903 | 0 | Q01, Q03, Q04, Q06, Q07, Q08, Q09, Q11, Q13, Q15, Q20 |
| whatsapp_resolve_card_or_category | 2 | 2 | — | 850 / 1017 | 1,173 | 0 | Q12, Q13 |
