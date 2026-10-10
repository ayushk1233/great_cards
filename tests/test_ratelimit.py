"""RateLimiter: sliding window, min interval, 429 cooldown, cross-process state (no network)."""

import asyncio

import pytest

from app.mcp.ratelimit import RateLimiter


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += s


def test_window_caps_requests():
    c = Clock()
    rl = RateLimiter(3, 60, clock=c)
    assert [rl.try_acquire() for _ in range(3)] == [0.0, 0.0, 0.0]
    assert rl.try_acquire() == pytest.approx(60)      # 4th waits for the oldest to leave the window
    c.t += 60
    assert rl.try_acquire() == 0.0


def test_min_interval_spaces_requests():
    c = Clock()
    rl = RateLimiter(100, 60, min_interval_s=0.5, clock=c)
    assert rl.try_acquire() == 0.0
    assert rl.try_acquire() == pytest.approx(0.5)
    c.t += 0.5
    assert rl.try_acquire() == 0.0


def test_429_cooldown_blocks_everyone():
    c = Clock()
    rl = RateLimiter(100, 60, clock=c)
    rl.penalize(30)
    assert rl.try_acquire() == pytest.approx(30)
    assert rl.snapshot()["throttled_429"] == 1


def test_wait_for_capacity_reserves_a_turn_without_taking_slots():
    c = Clock()
    rl = RateLimiter(10, 60, clock=c)
    for _ in range(5):
        rl.try_acquire()
    assert rl.wait_for_capacity(5, sleep=c.sleep) == 0.0
    assert rl.wait_for_capacity(6, sleep=c.sleep) == pytest.approx(60)
    assert rl.snapshot()["in_window"] == 0            # waiting doesn't consume


def test_state_file_is_shared_across_instances(tmp_path):
    c = Clock()
    path = tmp_path / "rl.json"
    a = RateLimiter(2, 60, state_path=path, clock=c)
    b = RateLimiter(2, 60, state_path=path, clock=c)   # e.g. a restarted runner or the UI
    a.try_acquire()
    a.try_acquire()
    assert b.try_acquire() > 0                          # b sees a's requests
    b.penalize(10)
    c.t += 61
    assert a.try_acquire() == 0.0                       # cooldown (10 s) long over


def test_corrupt_state_file_starts_fresh(tmp_path):
    path = tmp_path / "rl.json"
    path.write_text("{not json")
    assert RateLimiter(2, 60, state_path=path).try_acquire() == 0.0


def test_async_acquire_waits():
    c = Clock()
    rl = RateLimiter(1, 0.05, clock=__import__("time").time)
    asyncio.run(rl.acquire())
    asyncio.run(rl.acquire())                           # second one sleeps ~50 ms, then succeeds
    assert rl.stats["requests"] == 2 and rl.stats["waited_s"] > 0


def test_httpx_hook_penalizes_on_429():
    c = Clock()
    rl = RateLimiter(100, 60, clock=c)
    hook = rl.httpx_hooks(cooldown_s=45)["response"][0]

    class Resp:
        status_code, headers = 429, {}

    asyncio.run(hook(Resp()))
    assert rl.try_acquire() == pytest.approx(45)

    class RespRetry:
        status_code, headers = 429, {"retry-after": "90"}

    asyncio.run(hook(RespRetry()))
    assert rl.try_acquire() == pytest.approx(90)


def test_rejects_bad_config():
    with pytest.raises(ValueError):
        RateLimiter(0, 60)


def test_hooks_fire_on_every_real_http_request():
    """The hooks are wired into an httpx2 AsyncClient exactly as McpSession does (mock transport)."""
    import httpx2

    rl = RateLimiter(100, 60)
    statuses = iter([200, 429])
    transport = httpx2.MockTransport(lambda req: httpx2.Response(next(statuses)))

    async def go():
        async with httpx2.AsyncClient(transport=transport, event_hooks=rl.httpx_hooks(cooldown_s=0.01)) as c:
            await c.post("http://mcp.test/mcp", json={})
            await c.delete("http://mcp.test/mcp")

    asyncio.run(go())
    assert rl.stats["requests"] == 2 and rl.stats["throttled_429"] == 1


def test_mcp_session_passes_limiter_hooks(monkeypatch):
    """McpSession builds its HTTP client with the limiter's hooks (no connection is made)."""
    from app.mcp import client as mc

    seen = {}

    class Boom(Exception):
        pass

    def fake_stream(url, http_client=None, **kw):
        seen["hooks"] = http_client.event_hooks
        raise Boom

    monkeypatch.setattr(mc, "streamable_http_client", fake_stream)
    rl = RateLimiter(10, 60)
    with pytest.raises(Boom):
        asyncio.run(mc.McpSession("http://mcp.test/mcp", limiter=rl).__aenter__())
    assert len(seen["hooks"]["request"]) == 1 and len(seen["hooks"]["response"]) == 1


def test_call_tool_waits_for_cooldown_outside_the_sdk_timeout():
    """A 429 cooldown is waited out before the SDK call starts, so the request keeps its full
    read timeout instead of timing out while queued (no false 'unavailable')."""
    from app.mcp import client as mc

    rl = RateLimiter(100, 60)
    rl.penalize(0.2)
    seen = {}

    class FakeSdk:
        async def call_tool(self, name, args, read_timeout_seconds=None):
            seen["timeout"] = read_timeout_seconds
            seen["cooldown_left"] = rl.snapshot()["cooldown_s"]
            return {"content": [{"type": "text", "text": "{}"}]}

    s = mc.McpSession("http://mcp.test/mcp", timeout_s=20, limiter=rl)
    s._session = FakeSdk()
    res = asyncio.run(s.call_tool("list_cards", {}))
    assert res.ok and seen == {"timeout": 20, "cooldown_left": 0.0}
    assert rl.stats["waited_s"] >= 0.19
