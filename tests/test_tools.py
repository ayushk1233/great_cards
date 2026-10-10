"""Allowlisted specs are built verbatim from the recorded live catalog."""

import pytest

from app.mcp.tools import ALLOWLIST, MissingToolError, build_tool_specs


def test_allowlist_specs_are_verbatim(live_catalog):
    specs = build_tool_specs(live_catalog)
    by_name = {t["name"]: t for t in live_catalog}
    assert [s["function"]["name"] for s in specs] == list(ALLOWLIST)
    for s in specs:
        fn, src = s["function"], by_name[s["function"]["name"]]
        assert s["type"] == "function"
        assert fn["description"] == src["description"]
        expected = {k: v for k, v in src["inputSchema"].items() if k != "$schema"}
        assert fn["parameters"] == expected
        assert fn["parameters"]["type"] == "object"


def test_excluded_tools_not_exposed(live_catalog):
    names = {s["function"]["name"] for s in build_tool_specs(live_catalog)}
    assert "run_api_diagnostics" not in names
    assert "whatsapp_recommend_cards_for_spend_profile" not in names


def test_missing_tool_fails_loudly(live_catalog):
    trimmed = [t for t in live_catalog if t["name"] != "recommend_cards"]
    with pytest.raises(MissingToolError, match="recommend_cards"):
        build_tool_specs(trimmed)
