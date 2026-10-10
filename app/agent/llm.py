"""The only module that imports `openrouter`. Kept thin so tests swap in a fake.

chat(messages, tools) -> LlmReply. Messages are OpenAI-style role dicts; assistant tool
calls come back as plain dicts so the orchestrator can append them to history as-is.
"""

from dataclasses import dataclass, field

from openrouter import OpenRouter

from app.config import Settings


class LlmError(RuntimeError):
    pass


@dataclass
class LlmReply:
    text: str
    tool_calls: list[dict] = field(default_factory=list)  # [{"id","type","function":{"name","arguments"}}]
    finish_reason: str | None = None
    model: str | None = None
    usage: dict | None = None

    def as_message(self) -> dict:
        msg = {"role": "assistant", "content": self.text or ""}
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        return msg


def _text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    # list of content parts
    return "".join(getattr(p, "text", "") or (p.get("text", "") if isinstance(p, dict) else "") for p in content)


class OpenRouterLlm:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client = OpenRouter(api_key=settings.openrouter_api_key)

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> LlmReply:
        kwargs = dict(messages=messages, model=self.settings.llm_model,
                      temperature=self.settings.temperature, timeout_ms=60_000)
        if tools:
            kwargs.update(tools=tools, tool_choice="auto", parallel_tool_calls=False)
        try:
            res = self._client.chat.send(**kwargs)
        except Exception as e:  # SDK raises typed HTTP errors; surface one kind upward
            raise LlmError(f"{type(e).__name__}: {e}") from e

        if not res.choices:
            raise LlmError("LLM returned no choices")
        choice = res.choices[0]
        msg = choice.message
        calls = [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"}}
            for tc in (msg.tool_calls or [])
        ]
        usage = res.usage.model_dump(exclude_none=True) if res.usage else None
        return LlmReply(text=_text(msg.content), tool_calls=calls,
                        finish_reason=str(choice.finish_reason) if choice.finish_reason else None,
                        model=res.model, usage=usage)
