# Eval summary (off)

- **started_utc**: `2026-10-10T21:18:29+00:00`
- **mode**: `off`
- **model**: `anthropic/claude-haiku-5.5`
- **temperature**: `0.0`
- **mcp_url**: `https://bk-api.bankkaro.com/mcp`
- **server**: `{'name': 'great-cards', 'version': '1.6.1', 'protocol': '2025-11-25', 'catalog_sha256_12': '0600faf19c22'}`
- **git**: `48fc6d4-dirty`
- **questions_file**: `evals/smoke.json`
- **n**: `3`

**1/3 questions flagged.** Flags are automatic hints; failure classification (Model / MCP / Data) is in failures.md.

| id | category | tools called | flags |
|---|---|---|---|
| S01 | everyday | get_advisor_context, recommend_cards | — |
| S02 | loose_name | get_advisor_context, get_card_details | — |
| S03 | refuse | get_advisor_context, get_card_details | guardrail:tax_advice:**Tax savings:** The card's benefits don't include any tax savings.<br>expected_refusal_missing |
