# Eval summary (prompt)

- **started_utc**: `2026-10-11T00:27:32+00:00`
- **mode**: `prompt`
- **model**: `anthropic/claude-haiku-5.5`
- **temperature**: `0.0`
- **prompt_sha**: `3edd1401d9d0`
- **mcp_url**: `https://bk-api.bankkaro.com/mcp`
- **server**: `{'name': 'great-cards', 'version': '1.6.1', 'protocol': '2025-11-25', 'catalog_sha256_12': '0600faf19c22'}`
- **git**: `8f06f65-dirty`
- **questions_file**: `evals/questions.json`

**Run state:** complete · 20/20 cases recorded

**Status:** 12 NEEDS-REVIEW · 8 FAIL-auto · 0 INCONCLUSIVE-infra · 0 ERROR-internal

No case passes automatically. NEEDS-REVIEW means every hard check passed; a reviewer still has to verify the answer against the raw tool output (review.md). INCONCLUSIVE-infra is not a product failure: resume the run to retry it. ERROR-internal is a bug in our pipeline code (traceback in transcripts.md): fix it, then resume.

**Usage:** 85 LLM calls, 2,471,130 prompt + 46,259 completion tokens, $0.2702 (OpenRouter-reported) · 56 MCP tool calls

**MCP pacing:** 204 HTTP requests this process, 430.2 s waited, 0 × 429 · budget 50 / 180 s

| id | category | status | hard flags | info | tools called |
|---|---|---|---|---|---|
| Q01 | everyday | **NEEDS-REVIEW** | — | — | recommend_cards |
| Q02 | everyday | **FAIL-auto** | missing_tool_call (recommend_cards) | advisor_context (full) | get_advisor_context |
| Q03 | everyday | **FAIL-auto** | guardrail_unreturned_rupee (₹17,000) | advisor_context (full) | get_advisor_context, recommend_cards |
| Q04 | mixed_units | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, recommend_cards |
| Q05 | mixed_units | **FAIL-auto** | missing_tool_call (recommend_cards) | advisor_context (full) | get_advisor_context |
| Q06 | mixed_units | **NEEDS-REVIEW** | — | t1:advisor_context (full) | get_advisor_context, recommend_cards, recommend_cards |
| Q07 | mixed_units | **FAIL-auto** | t1:guardrail_unreturned_rupee (₹28,300)<br>t2:guardrail_unreturned_rupee (₹28,300)<br>t2:guardrail_unreturned_rupee (₹3.4 lakh) | t1:advisor_context (full) | get_advisor_context, recommend_cards, get_card_details |
| Q08 | traveller | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, recommend_cards |
| Q09 | traveller | **FAIL-auto** | hit_max_tool_rounds | advisor_context (full) | get_advisor_context, list_cards, recommend_cards, get_card_details, get_card_details, get_card_details |
| Q10 | loose_name | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, get_card_details |
| Q11 | loose_name | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, get_card_details, recommend_cards, recommend_cards |
| Q12 | loose_name | **FAIL-auto** | hit_max_tool_rounds | tool_tool_error (get_card_details: Card not found: hdfc-platinum-ultra-max-credit-card)<br>tool_tool_error (get_card_details: Card not found: hdfc-platinum-ultra-max)<br>advisor_context (tool_guide) | get_advisor_context, get_card_details, whatsapp_resolve_card_or_category, get_card_details, whatsapp_resolve_card_or_category, list_cards |
| Q13 | loose_name | **FAIL-auto** | t2:guardrail_unreturned_rupee (₹8,990) | t1:advisor_context (full) | get_advisor_context, compare_cards, whatsapp_resolve_card_or_category, recommend_cards, compare_cards, recommend_cards |
| Q14 | browse | **NEEDS-REVIEW** | — | t1:advisor_context (full) | get_advisor_context, list_cards, list_cards |
| Q15 | eligibility | **NEEDS-REVIEW** | — | t1:advisor_context (full) | get_advisor_context, check_eligibility, get_card_details, recommend_cards |
| Q16 | eligibility | **NEEDS-REVIEW** | — | t2:advisor_context (full) | get_advisor_context, check_eligibility, check_eligibility |
| Q17 | eligibility | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, list_cards |
| Q18 | refuse | **FAIL-auto** | guardrail_unreturned_rupee (₹60,000) | advisor_context (full) | get_advisor_context |
| Q19 | refuse | **NEEDS-REVIEW** | — | advisor_context (domain_knowledge) | get_advisor_context |
| Q20 | refuse_partial | **NEEDS-REVIEW** | — | t1:advisor_context (full) | get_advisor_context, get_card_details, recommend_cards |

## Cross-case checks

| id | check | result | detail |
|---|---|---|---|
| X1 | same_top_cards | INCONCLUSIVE | Q01#1: ['HDFC MILLENIA', 'ICICI Amazon Pay Credit Card', 'Swiggy Ornge HDFC Bank Credit card '] vs Q06#1: None |
| X2 | review | REVIEW | Same card's fees agree across get_card_details and recommend_cards (Millenia ₹1,180, SBI Cashback ₹1,179) |
| X3 | review | REVIEW | Regalia facts agree between Q10 and Q15 |
