"""Live MCP tool schemas -> OpenRouter function-tool specs.

Descriptions and input schemas are passed through verbatim from tools/list (only the
JSON-Schema `$schema` meta key is dropped). Nothing here is hand-written, so the model
sees exactly what the server advertises, quirks included.
"""

# 6 core tools + the alias resolver (decision recorded in PROGRESS.md).
# Excluded: other whatsapp_* facades (hide milestones, garble benefits), generate_content_brief,
# run_api_diagnostics (operator tools).
ALLOWLIST = (
    "get_advisor_context",
    "recommend_cards",
    "get_card_details",
    "list_cards",
    "compare_cards",
    "check_eligibility",
    "whatsapp_resolve_card_or_category",
)


class MissingToolError(RuntimeError):
    pass


def to_function_spec(tool: dict) -> dict:
    schema = {k: v for k, v in (tool.get("inputSchema") or {}).items() if k != "$schema"}
    schema.setdefault("type", "object")
    schema.setdefault("properties", {})
    return {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool.get("description") or "",
            "parameters": schema,
        },
    }


def build_tool_specs(live_tools: list[dict], allowlist: tuple[str, ...] = ALLOWLIST) -> list[dict]:
    """Filter the live catalog to the allowlist (in allowlist order). Fails loudly if the
    server stopped advertising a tool we depend on, rather than silently degrading."""
    by_name = {t["name"]: t for t in live_tools}
    missing = [n for n in allowlist if n not in by_name]
    if missing:
        raise MissingToolError(f"MCP server no longer advertises: {missing}")
    return [to_function_spec(by_name[n]) for n in allowlist]
