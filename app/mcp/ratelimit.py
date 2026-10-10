"""Client-side pacing for the production MCP server (it rate-limits at ~65 requests / 3 min).

Counts every real HTTP request (initialize, notifications, the GET stream, tools/list,
tools/call, the closing DELETE) through an httpx request hook, so the budget can't be
undercounted by session overhead. A 429 puts every caller into a cooldown.

With `state_path`, the sliding window and the cooldown live in a small JSON file guarded by
an exclusive file lock, so separate processes (eval runner, UI, a restarted runner) share
one budget and a restart never bursts.
"""

import asyncio
import fcntl
import json
import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path


class RateLimiter:
    def __init__(self, max_requests: int, window_s: float, min_interval_s: float = 0.0,
                 state_path: str | Path | None = None, clock=time.time):
        if max_requests < 1 or window_s <= 0:
            raise ValueError("max_requests must be >= 1 and window_s > 0")
        self.max_requests, self.window_s, self.min_interval_s = max_requests, window_s, min_interval_s
        self.state_path = Path(state_path) if state_path else None
        self._clock = clock
        self._thread_lock = threading.Lock()
        self._mem = {"stamps": [], "cooldown_until": 0.0}
        self.stats = {"requests": 0, "waited_s": 0.0, "throttled_429": 0}
        if self.state_path:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ state
    @contextmanager
    def _locked_state(self):
        with self._thread_lock:
            if not self.state_path:
                yield self._mem
                return
            fd = os.open(self.state_path, os.O_RDWR | os.O_CREAT, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX)
                raw = os.read(fd, 1 << 20)
                try:
                    state = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    state = {}  # corrupt file: start a fresh window rather than crash
                state.setdefault("stamps", [])
                state.setdefault("cooldown_until", 0.0)
                yield state
                data = json.dumps(state).encode()
                os.lseek(fd, 0, os.SEEK_SET)
                os.ftruncate(fd, 0)
                os.write(fd, data)
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)

    def _wait_needed(self, state: dict, now: float, slots: int) -> float:
        state["stamps"] = [t for t in state["stamps"] if now - t < self.window_s]
        stamps = state["stamps"]
        waits = [state["cooldown_until"] - now]
        if len(stamps) + slots > self.max_requests:
            # wait until enough of the oldest stamps leave the window
            idx = len(stamps) + slots - self.max_requests - 1
            waits.append(stamps[min(idx, len(stamps) - 1)] + self.window_s - now if stamps else 0.0)
        if stamps:
            waits.append(stamps[-1] + self.min_interval_s - now)
        return max(0.0, *waits)

    # ------------------------------------------------------------------ API
    def try_acquire(self) -> float:
        """Take one slot if available. Returns 0.0 on success, else seconds to wait."""
        with self._locked_state() as state:
            now = self._clock()
            wait = self._wait_needed(state, now, 1)
            if wait <= 0:
                state["stamps"].append(now)
                self.stats["requests"] += 1
            return wait

    async def acquire(self) -> None:
        while (wait := self.try_acquire()) > 0:
            self.stats["waited_s"] += wait
            await asyncio.sleep(wait)

    def wait_for_capacity(self, slots: int, sleep=time.sleep) -> float:
        """Block (without taking slots) until `slots` requests fit in the window and no cooldown
        is active. The runner calls this before each turn so a turn rarely stalls mid-flight."""
        slots = min(slots, self.max_requests)
        total = 0.0
        while True:
            with self._locked_state() as state:
                wait = self._wait_needed(state, self._clock(), slots)
            if wait <= 0:
                return total
            total += wait
            self.stats["waited_s"] += wait
            sleep(wait)

    async def wait_ready(self, slots: int = 1) -> float:
        """Async wait_for_capacity. McpSession calls it *before* each request so that waiting for
        the window or a 429 cooldown never counts against the SDK's per-request timeout; the
        request hook then only pays the min interval."""
        slots = min(slots, self.max_requests)
        total = 0.0
        while True:
            with self._locked_state() as state:
                wait = self._wait_needed(state, self._clock(), slots)
            if wait <= 0:
                return total
            total += wait
            self.stats["waited_s"] += wait
            await asyncio.sleep(wait)

    def penalize(self, seconds: float) -> None:
        """Server said 429: nobody sends anything for `seconds`."""
        self.stats["throttled_429"] += 1
        with self._locked_state() as state:
            state["cooldown_until"] = max(state["cooldown_until"], self._clock() + seconds)

    def snapshot(self) -> dict:
        with self._locked_state() as state:
            now = self._clock()
            in_window = sum(1 for t in state["stamps"] if now - t < self.window_s)
            cooldown = max(0.0, state["cooldown_until"] - now)
        return {"in_window": in_window, "max_requests": self.max_requests, "window_s": self.window_s,
                "cooldown_s": round(cooldown, 1), **{k: round(v, 1) if isinstance(v, float) else v
                                                      for k, v in self.stats.items()}}

    # ------------------------------------------------------------------ httpx hooks
    def httpx_hooks(self, cooldown_s: float = 60.0) -> dict:
        async def on_request(request):
            await self.acquire()

        async def on_response(response):
            if response.status_code == 429:
                retry_after = response.headers.get("retry-after", "")
                self.penalize(float(retry_after) if retry_after.replace(".", "", 1).isdigit() else cooldown_s)

        return {"request": [on_request], "response": [on_response]}
