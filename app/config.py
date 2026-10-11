"""Settings from environment / .env. Import-safe: nothing is validated until load_settings()."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str
    llm_model: str
    mcp_url: str
    guardrails: str  # "off" = report only, "prompt" = rule prompt only, "on" = prompt + enforce
    max_tool_rounds: int = 6
    max_tool_calls_per_turn: int = 6  # MCP calls per turn; extra calls are refused, not sent
    tool_timeout_s: float = 20.0
    turn_deadline_s: float = 180.0    # whole turn (LLM + tools + rate-limit waits)
    temperature: float = 0.0
    # client-side pacing of the production MCP server (it limits at ~65 HTTP requests / 3 min)
    mcp_max_requests: int = 50
    mcp_window_s: float = 180.0
    mcp_min_interval_s: float = 0.5
    mcp_rate_state: str = ""          # shared state file; "" = in-process only
    catalog_ttl_s: float = 600.0      # tools/list cached per process for this long


class ConfigError(RuntimeError):
    pass


def load_settings(require_key: bool = True) -> Settings:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if require_key and not key:
        raise ConfigError("OPENROUTER_API_KEY is missing. Copy .env.example to .env and set it.")
    guardrails = os.getenv("GUARDRAILS", "off").strip().lower()
    if guardrails not in ("off", "prompt", "on"):
        raise ConfigError(f"GUARDRAILS must be 'off', 'prompt' or 'on', got {guardrails!r}")
    return Settings(
        openrouter_api_key=key,
        llm_model=os.getenv("LLM_MODEL", "anthropic/claude-haiku-5.5").strip(),
        mcp_url=os.getenv("MCP_URL", "https://bk-api.bankkaro.com/mcp").strip(),
        guardrails=guardrails,
        max_tool_calls_per_turn=_num("MAX_TOOL_CALLS_PER_TURN", 6, int),
        turn_deadline_s=_num("TURN_DEADLINE_S", 180.0, float),
        mcp_max_requests=_num("MCP_MAX_REQUESTS", 50, int),
        mcp_window_s=_num("MCP_WINDOW_S", 180.0, float),
        mcp_min_interval_s=_num("MCP_MIN_INTERVAL_S", 0.5, float),
        mcp_rate_state=os.getenv("MCP_RATE_STATE", str(ROOT / ".cache" / "mcp_ratelimit.json")).strip(),
        catalog_ttl_s=_num("CATALOG_TTL_S", 600.0, float),
    )


def _num(name: str, default, cast):
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = cast(raw)
    except ValueError:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from None
    if value <= 0 and name != "MCP_MIN_INTERVAL_S":
        raise ConfigError(f"{name} must be positive, got {raw!r}")
    return value


def build_limiter(settings: Settings):
    from app.mcp.ratelimit import RateLimiter

    return RateLimiter(settings.mcp_max_requests, settings.mcp_window_s, settings.mcp_min_interval_s,
                       state_path=settings.mcp_rate_state or None)
