"""Anti-corruption layer over the Anthropic SDK: everything downstream
(stage_runner.py, and every test) only ever sees TextBlock / ToolUseBlock /
ModelResponse, never the SDK's own response types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Union

from loguru import logger


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


# A stage turn can legitimately produce a long document (e.g. a full stage
# 04 adaptation draft). 64k leaves headroom well under Sonnet 5's 128k output
# ceiling while keeping most turns nowhere near the limit.
DEFAULT_MAX_TOKENS = 64_000


def _with_trailing_cache_breakpoint(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark the end of the (growing) message history as a cache breakpoint,
    on top of the one the caller already put on the static system prompt.

    Without this, only the system prompt's frozen prose is ever cached --
    every tool-result round trip within a stage's up-to-30-iteration loop
    re-sends and re-bills the entire accumulated transcript as fresh input.
    Copies rather than mutates, since `messages` here is the same list of
    dicts backing the on-disk transcript.
    """
    if not messages or not messages[-1].get("content"):
        return messages
    *rest, last = messages
    *earlier_blocks, last_block = last["content"]
    marked_block = {**last_block, "cache_control": {"type": "ephemeral"}}
    return [*rest, {**last, "content": [*earlier_blocks, marked_block]}]


class AnthropicModelClient:
    """Wraps the real Anthropic SDK. Pass `client` in tests to substitute a
    fake with the same `.messages.stream(...)` shape."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-5",
        client: Any = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ):
        if client is not None:
            self._client = client
        else:
            import anthropic

            self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def create(self, system, messages, tools) -> ModelResponse:
        logger.debug(f"anthropic request: model={self._model} messages={len(messages)} tools={len(tools)}")
        # Streaming (rather than a single blocking create()) is required at
        # this max_tokens size -- a non-streaming call this large risks the
        # HTTP connection timing out before Claude finishes, which would
        # surface as a transport error instead of a clean response.
        with self._client.messages.stream(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=_with_trailing_cache_breakpoint(messages),
            tools=tools,
        ) as stream:
            response = stream.get_final_message()
        logger.debug(
            f"anthropic response: stop_reason={response.stop_reason} blocks={len(response.content)} "
            f"cache_read={getattr(response.usage, 'cache_read_input_tokens', None)} "
            f"cache_write={getattr(response.usage, 'cache_creation_input_tokens', None)}"
        )
        content: list[ContentBlock] = []
        for block in response.content:
            if block.type == "text":
                content.append(TextBlock(text=block.text))
            elif block.type == "tool_use":
                content.append(ToolUseBlock(id=block.id, name=block.name, input=block.input))
        return ModelResponse(content=content, stop_reason=response.stop_reason)
