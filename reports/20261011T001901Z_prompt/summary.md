# Eval summary (prompt)

- **started_utc**: `2026-10-11T00:19:01+00:00`
- **mode**: `prompt`
- **model**: `anthropic/claude-haiku-5.5`
- **temperature**: `0.0`
- **prompt_sha**: `e8b8e468424f`
- **mcp_url**: `https://bk-api.bankkaro.com/mcp`
- **server**: `{'name': 'great-cards', 'version': '1.6.1', 'protocol': '2025-11-25', 'catalog_sha256_12': '0600faf19c22'}`
- **git**: `e2571f3-dirty`
- **questions_file**: `evals/questions.json`

**Run state:** partial · 4/20 cases recorded

**Status:** 2 NEEDS-REVIEW · 2 FAIL-auto · 0 INCONCLUSIVE-infra · 0 ERROR-internal

No case passes automatically. NEEDS-REVIEW means every hard check passed; a reviewer still has to verify the answer against the raw tool output (review.md). INCONCLUSIVE-infra is not a product failure: resume the run to retry it. ERROR-internal is a bug in our pipeline code (traceback in transcripts.md): fix it, then resume.

**Usage:** 20 LLM calls, 489,756 prompt + 16,132 completion tokens, $0.0570 (OpenRouter-reported) · 14 MCP tool calls

**MCP pacing:** 47 HTTP requests this process, 72.2 s waited, 0 × 429 · budget 50 / 180 s

| id | category | status | hard flags | info | tools called |
|---|---|---|---|---|---|
| Q03 | everyday | **FAIL-auto** | guardrail_unreturned_rupee (₹17,000) | advisor_context (full) | get_advisor_context, recommend_cards |
| Q07 | mixed_units | **NEEDS-REVIEW** | — | t1:advisor_context (full) | get_advisor_context, recommend_cards, get_card_details, get_card_details |
| Q09 | traveller | **FAIL-auto** | hit_max_tool_rounds | advisor_context (domain_knowledge) | get_advisor_context, list_cards, recommend_cards, get_card_details, get_card_details, get_card_details |
| Q20 | refuse_partial | **NEEDS-REVIEW** | — | — | get_card_details, recommend_cards |

## Cross-case checks

| id | check | result | detail |
|---|---|---|---|
| X1 | same_top_cards | INCONCLUSIVE | Q01#1: None vs Q06#1: None |
| X2 | review | REVIEW | Same card's fees agree across get_card_details and recommend_cards (Millenia ₹1,180, SBI Cashback ₹1,179) |
| X3 | review | REVIEW | Regalia facts agree between Q10 and Q15 |
