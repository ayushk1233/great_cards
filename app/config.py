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
    guardrails: str  # "off" = report only, "on" = enforce
    max_tool_rounds: int = 6
    tool_timeout_s: float = 20.0
    temperature: float = 0.0


class ConfigError(RuntimeError):
    pass


def load_settings(require_key: bool = True) -> Settings:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if require_key and not key:
        raise ConfigError("OPENROUTER_API_KEY is missing. Copy .env.example to .env and set it.")
    guardrails = os.getenv("GUARDRAILS", "off").strip().lower()
    if guardrails not in ("off", "on"):
        raise ConfigError(f"GUARDRAILS must be 'off' or 'on', got {guardrails!r}")
    return Settings(
        openrouter_api_key=key,
        llm_model=os.getenv("LLM_MODEL", "anthropic/claude-haiku-5.5").strip(),
        mcp_url=os.getenv("MCP_URL", "https://bk-api.bankkaro.com/mcp").strip(),
        guardrails=guardrails,
    )
