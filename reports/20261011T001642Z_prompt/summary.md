# Eval summary (prompt)

- **started_utc**: `2026-10-11T00:16:42+00:00`
- **mode**: `prompt`
- **model**: `anthropic/claude-haiku-5.5`
- **temperature**: `0.0`
- **prompt_sha**: `da87501526fc`
- **mcp_url**: `https://bk-api.bankkaro.com/mcp`
- **server**: `{'name': 'great-cards', 'version': '1.6.1', 'protocol': '2025-11-25', 'catalog_sha256_12': '0600faf19c22'}`
- **git**: `e2571f3-dirty`
- **questions_file**: `evals/questions.json`

**Run state:** partial · 2/20 cases recorded

**Status:** 1 NEEDS-REVIEW · 1 FAIL-auto · 0 INCONCLUSIVE-infra · 0 ERROR-internal

No case passes automatically. NEEDS-REVIEW means every hard check passed; a reviewer still has to verify the answer against the raw tool output (review.md). INCONCLUSIVE-infra is not a product failure: resume the run to retry it. ERROR-internal is a bug in our pipeline code (traceback in transcripts.md): fix it, then resume.

**Usage:** 12 LLM calls, 390,248 prompt + 10,484 completion tokens, $0.0443 (OpenRouter-reported) · 9 MCP tool calls

**MCP pacing:** 28 HTTP requests this process, 8.4 s waited, 0 × 429 · budget 50 / 180 s

| id | category | status | hard flags | info | tools called |
|---|---|---|---|---|---|
| Q07 | mixed_units | **NEEDS-REVIEW** | — | t1:advisor_context (full) | get_advisor_context, recommend_cards, get_card_details |
| Q09 | traveller | **FAIL-auto** | hit_max_tool_rounds | advisor_context (full) | get_advisor_context, list_cards, recommend_cards, get_card_details, get_card_details, get_card_details |

## Cross-case checks

| id | check | result | detail |
|---|---|---|---|
| X1 | same_top_cards | INCONCLUSIVE | Q01#1: None vs Q06#1: None |
| X2 | review | REVIEW | Same card's fees agree across get_card_details and recommend_cards (Millenia ₹1,180, SBI Cashback ₹1,179) |
| X3 | review | REVIEW | Regalia facts agree between Q10 and Q15 |
