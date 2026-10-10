"""Single read-only call to the real server: tools/list. Skipped unless `pytest -m live`."""

import asyncio

import pytest

from app.config import load_settings
from app.mcp.client import McpSession
from app.mcp.tools import build_tool_specs


@pytest.mark.live
def test_live_catalog_has_allowlist():
    async def go():
        async with McpSession(load_settings(require_key=False).mcp_url) as s:
            return s.server_info, await s.list_tools()

    info, tools = asyncio.run(go())
    assert info["name"] == "great-cards"
    assert len(build_tool_specs(tools)) == 7
