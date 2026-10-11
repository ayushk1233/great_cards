# Eval summary (prompt)

- **started_utc**: `2026-10-10T23:56:31+00:00`
- **mode**: `prompt`
- **model**: `anthropic/claude-haiku-5.5`
- **temperature**: `0.0`
- **prompt_sha**: `da87501526fc`
- **mcp_url**: `https://bk-api.bankkaro.com/mcp`
- **server**: `{'name': 'great-cards', 'version': '1.6.1', 'protocol': '2025-11-25', 'catalog_sha256_12': '0600faf19c22'}`
- **git**: `da67eea-dirty`
- **questions_file**: `evals/questions.json`

**Run state:** partial · 9/20 cases recorded

**Status:** 4 NEEDS-REVIEW · 5 FAIL-auto · 0 INCONCLUSIVE-infra · 0 ERROR-internal

No case passes automatically. NEEDS-REVIEW means every hard check passed; a reviewer still has to verify the answer against the raw tool output (review.md). INCONCLUSIVE-infra is not a product failure: resume the run to retry it. ERROR-internal is a bug in our pipeline code (traceback in transcripts.md): fix it, then resume.

**Usage:** 36 LLM calls, 1,070,182 prompt + 22,178 completion tokens, $0.1181 (OpenRouter-reported) · 24 MCP tool calls

**MCP pacing:** 87 HTTP requests this process, 195.4 s waited, 0 × 429 · budget 50 / 180 s

| id | category | status | hard flags | info | tools called |
|---|---|---|---|---|---|
| Q01 | everyday | **FAIL-auto** | missing_tool_call (recommend_cards) | advisor_context (full) | get_advisor_context |
| Q03 | everyday | **FAIL-auto** | guardrail_unreturned_rupee (₹2.04 lakh)<br>guardrail_unreturned_rupee (₹17,000) | advisor_context (full) | get_advisor_context, recommend_cards, get_card_details |
| Q05 | mixed_units | **FAIL-auto** | missing_tool_call (recommend_cards) | advisor_context (full) | get_advisor_context |
| Q07 | mixed_units | **FAIL-auto** | t1:guardrail_unreturned_rupee (₹28,300)<br>t1:guardrail_unreturned_rupee (₹3.4 lakh) | t1:advisor_context (full) | get_advisor_context, recommend_cards, get_card_details |
| Q09 | traveller | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, list_cards |
| Q10 | loose_name | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, get_card_details |
| Q11 | loose_name | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, get_card_details, recommend_cards, recommend_cards |
| Q13 | loose_name | **FAIL-auto** | t2:guardrail_unreturned_rupee (₹20,000)<br>t2:guardrail_unreturned_rupee (₹2.4 lakh) | t1:advisor_context (full) | get_advisor_context, compare_cards, whatsapp_resolve_card_or_category, compare_cards, recommend_cards |
| Q20 | refuse_partial | **NEEDS-REVIEW** | — | t1:advisor_context (full) | get_advisor_context, get_card_details, recommend_cards |

## Cross-case checks

| id | check | result | detail |
|---|---|---|---|
| X1 | same_top_cards | INCONCLUSIVE | Q01#1: None vs Q06#1: None |
| X2 | review | REVIEW | Same card's fees agree across get_card_details and recommend_cards (Millenia ₹1,180, SBI Cashback ₹1,179) |
| X3 | review | REVIEW | Regalia facts agree between Q10 and Q15 |
