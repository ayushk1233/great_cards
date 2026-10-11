# Eval summary (off)

- **started_utc**: `2026-10-10T23:51:27+00:00`
- **mode**: `off`
- **model**: `anthropic/claude-haiku-5.5`
- **temperature**: `0.0`
- **prompt_sha**: `2f7726b5dcad`
- **mcp_url**: `https://bk-api.bankkaro.com/mcp`
- **server**: `{'name': 'great-cards', 'version': '1.6.1', 'protocol': '2025-11-25', 'catalog_sha256_12': '0600faf19c22'}`
- **git**: `da67eea-dirty`
- **questions_file**: `evals/questions.json`

**Run state:** partial · 9/20 cases recorded

**Status:** 1 NEEDS-REVIEW · 8 FAIL-auto · 0 INCONCLUSIVE-infra · 0 ERROR-internal

No case passes automatically. NEEDS-REVIEW means every hard check passed; a reviewer still has to verify the answer against the raw tool output (review.md). INCONCLUSIVE-infra is not a product failure: resume the run to retry it. ERROR-internal is a bug in our pipeline code (traceback in transcripts.md): fix it, then resume.

**Usage:** 40 LLM calls, 1,219,454 prompt + 26,035 completion tokens, $0.1350 (OpenRouter-reported) · 28 MCP tool calls

**MCP pacing:** 91 HTTP requests this process, 107.2 s waited, 0 × 429 · budget 50 / 180 s

| id | category | status | hard flags | info | tools called |
|---|---|---|---|---|---|
| Q01 | everyday | **FAIL-auto** | missing_tool_call (recommend_cards) | advisor_context (full) | get_advisor_context |
| Q03 | everyday | **FAIL-auto** | guardrail_unreturned_rupee (₹17,000)<br>guardrail_unreturned_rupee (₹2.04 lakh)<br>guardrail_unreturned_rupee (₹9,600)<br>guardrail_unreturned_rupee (₹9,200) | advisor_context (full) | get_advisor_context, recommend_cards, get_card_details |
| Q05 | mixed_units | **FAIL-auto** | missing_tool_call (recommend_cards) | advisor_context (full) | get_advisor_context |
| Q07 | mixed_units | **FAIL-auto** | t1:guardrail_unreturned_rupee (₹22,000)<br>t1:guardrail_unreturned_rupee (₹3.4 lakh)<br>t1:guardrail_unreturned_rupee (₹6,800)<br>t2:guardrail_unreturned_rupee (₹2,700)<br>t2:guardrail_unreturned_rupee (₹2,700)<br>t2:guardrail_unreturned_rupee (₹2.6 lakh)<br>t2:guardrail_unreturned_rupee (₹22,000) | t1:advisor_context (full) | get_advisor_context, recommend_cards, get_card_details, get_card_details, get_card_details |
| Q09 | traveller | **FAIL-auto** | guardrail_unreturned_rupee (₹8 lakh)<br>guardrail_unreturned_rupee (₹8 lakh)<br>guardrail_unreturned_rupee (₹11,900)<br>guardrail_unreturned_rupee (₹11,900)<br>guardrail_unreturned_rupee (₹8 lakh) | advisor_context (full) | get_advisor_context, list_cards, recommend_cards, get_card_details, get_card_details |
| Q10 | loose_name | **NEEDS-REVIEW** | — | advisor_context (full) | get_advisor_context, get_card_details |
| Q11 | loose_name | **FAIL-auto** | guardrail_unreturned_rupee (₹24,000) | advisor_context (full) | get_advisor_context, get_card_details, recommend_cards, compare_cards |
| Q13 | loose_name | **FAIL-auto** | t2:guardrail_unreturned_rupee (₹8,400)<br>t2:guardrail_unreturned_rupee (₹2,900)<br>t2:guardrail_unreturned_rupee (₹11,900) | t1:advisor_context (full) | get_advisor_context, compare_cards, compare_cards, recommend_cards |
| Q20 | refuse_partial | **FAIL-auto** | t1:guardrail_unreturned_rupee (₹8,820) | t1:advisor_context (full) | get_advisor_context, get_card_details, recommend_cards |

## Cross-case checks

| id | check | result | detail |
|---|---|---|---|
| X1 | same_top_cards | INCONCLUSIVE | Q01#1: None vs Q06#1: None |
| X2 | review | REVIEW | Same card's fees agree across get_card_details and recommend_cards (Millenia ₹1,180, SBI Cashback ₹1,179) |
| X3 | review | REVIEW | Regalia facts agree between Q10 and Q15 |
