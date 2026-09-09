"""Anti-corruption layer over the Anthropic SDK: everything downstream
(stage_runner.py, and every test) only ever sees TextBlock / ToolUseBlock /
ModelResponse, never the SDK's own response types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Union


@dataclass(frozen=True)
class TextBlock:
    text: str


@dataclass(frozen=True)
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]


ContentBlock = Union[TextBlock, ToolUseBlock]


@dataclass(frozen=True)
class ModelResponse:
    content: list[ContentBlock]
    stop_reason: str


class ModelClient(Protocol):
    def create(
        self,
        system: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelResponse: ...


class AnthropicModelClient:
    """Wraps the real Anthropic SDK. Pass `client` in tests to substitute a
    fake with the same `.messages.create(...)` shape."""

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-5", client: Any = None):
        if client is not None:
            self._client = client
        else:
            import anthropic

            self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def create(self, system, messages, tools) -> ModelResponse:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=16000,
            system=system,
            messages=messages,
            tools=tools,
        )
        content: list[ContentBlock] = []
        for block in response.content:
            if block.type == "text":
                content.append(TextBlock(text=block.text))
            elif block.type == "tool_use":
                content.append(ToolUseBlock(id=block.id, name=block.name, input=block.input))
        return ModelResponse(content=content, stop_reason=response.stop_reason)
