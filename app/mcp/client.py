"""The only module that touches the MCP SDK.

One session per chat turn (`async with McpSession(url) as s:`), sequential calls only,
and every outcome normalised into a ToolResult so callers never see SDK exceptions.

Verified server quirks handled here (evidence: discovery/FINDINGS.md):
  - validation failures come back as isError=true with "MCP error -32602: ..." text
  - "not found" comes back as {"error": "..."} with isError=false
  - HTTP 429 surfaces as MCPError(-32603, 'Server returned an error response')
"""

import asyncio
import json
import time
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any

from mcp import ClientSession, types
from mcp.client.streamable_http import streamable_http_client

RETRY_BACKOFF_S = 3.0

# error_kind values
TOOL_ERROR = "tool_error"     # server rejected the call or reported an error payload
MALFORMED = "malformed"       # result was not the JSON we expect
UNAVAILABLE = "unavailable"   # transport / rate limit / timeout, after retry


@dataclass
class ToolResult:
    ok: bool
    data: Any = None              # parsed JSON when ok
    error_kind: str | None = None
    error_msg: str | None = None
    raw_text: str | None = None   # verbatim text content, kept for the trace
    latency_ms: int = 0
    raw_result: dict | None = field(default=None, repr=False)  # full protocol dump

    def for_model(self) -> str:
        """What the LLM sees as the tool message content."""
        if self.ok:
            return json.dumps(self.data, ensure_ascii=False, separators=(",", ":"))
        return json.dumps({"error": self.error_kind, "message": self.error_msg}, ensure_ascii=False)


def _dump(obj) -> dict:
    return obj.model_dump(mode="json", by_alias=True, exclude_none=True) if hasattr(obj, "model_dump") else obj


def normalize(raw_result: dict, latency_ms: int = 0) -> ToolResult:
    """Turn a CallToolResult dump (protocol camelCase) into a ToolResult. Pure; tested offline."""
    texts = [c.get("text") for c in raw_result.get("content", []) if c.get("type") == "text"]
    raw_text = "\n".join(t for t in texts if t is not None) or None
    base = dict(raw_text=raw_text, latency_ms=latency_ms, raw_result=raw_result)

    if raw_result.get("isError"):
        return ToolResult(ok=False, error_kind=TOOL_ERROR, error_msg=raw_text or "tool reported an error", **base)
    if not raw_text:
        return ToolResult(ok=False, error_kind=MALFORMED, error_msg="empty tool result", **base)
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return ToolResult(ok=False, error_kind=MALFORMED, error_msg="tool result was not JSON", **base)
    if isinstance(data, dict) and set(data) == {"error"}:
        return ToolResult(ok=False, error_kind=TOOL_ERROR, error_msg=str(data["error"]), **base)
    return ToolResult(ok=True, data=data, **base)


class McpSession:
    """Async context manager around one MCP session."""

    def __init__(self, url: str, timeout_s: float = 20.0):
        self.url = url
        self.timeout_s = timeout_s
        self.server_info: dict = {}
        self._stack = None
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "McpSession":
        self._stack = AsyncExitStack()
        try:
            read, write = await self._stack.enter_async_context(streamable_http_client(self.url))
            self._session = await self._stack.enter_async_context(ClientSession(read, write))
            init = await self._session.initialize()
        except BaseException:
            await self._stack.aclose()
            raise
        self.server_info = {
            "name": init.server_info.name,
            "version": init.server_info.version,
            "protocol": init.protocol_version,
        }
        return self

    async def __aexit__(self, *exc) -> None:
        try:
            await self._stack.aclose()
        except Exception:
            pass  # session teardown can be rate-limited too; never mask the turn's result

    async def list_tools(self) -> list[dict]:
        tools, cursor = [], None
        while True:
            params = types.PaginatedRequestParams(cursor=cursor) if cursor else None
            page = _dump(await self._session.list_tools(params=params))
            tools.extend(page.get("tools", []))
            cursor = page.get("nextCursor")
            if not cursor:
                return tools

    async def call_tool(self, name: str, arguments: dict) -> ToolResult:
        last_err = ""
        for attempt in range(2):  # one retry, never more: the server is production
            started = time.perf_counter()
            try:
                result = await self._session.call_tool(name, arguments, read_timeout_seconds=self.timeout_s)
                return normalize(_dump(result), round((time.perf_counter() - started) * 1000))
            except Exception as e:  # MCPError (incl. 429), timeouts, httpx transport errors
                last_err = repr(e)
                if attempt == 0:
                    await asyncio.sleep(RETRY_BACKOFF_S)
        return ToolResult(ok=False, error_kind=UNAVAILABLE,
                          error_msg=f"card service unavailable after retry: {last_err}")
