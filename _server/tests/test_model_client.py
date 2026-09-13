from types import SimpleNamespace

from app.model_client import DEFAULT_MAX_TOKENS, AnthropicModelClient, TextBlock, ToolUseBlock


class _FakeStream:
    def __init__(self, response):
        self._response = response

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def get_final_message(self):
        return self._response


class FakeSDKClient:
    """Stands in for anthropic.Anthropic -- only the .messages.stream shape
    that AnthropicModelClient depends on."""

    def __init__(self, sdk_response):
        if not hasattr(sdk_response, "usage"):
            sdk_response = SimpleNamespace(**vars(sdk_response), usage=SimpleNamespace())
        self._response = sdk_response
        self.messages = SimpleNamespace(stream=self._stream)
        self.last_call = None

    def _stream(self, **kwargs):
        self.last_call = kwargs
        return _FakeStream(self._response)


def test_converts_text_block():
    sdk_response = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hello")],
        stop_reason="end_turn",
    )
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk)

    result = client.create(system=[], messages=[], tools=[])

    assert result.content == [TextBlock(text="hello")]
    assert result.stop_reason == "end_turn"


def test_converts_tool_use_block():
    sdk_response = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", id="call_1", name="write_file", input={"path": "a.md"})],
        stop_reason="tool_use",
    )
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk)

    result = client.create(system=[], messages=[], tools=[])

    assert result.content == [ToolUseBlock(id="call_1", name="write_file", input={"path": "a.md"})]


def test_passes_system_messages_and_tools_through():
    sdk_response = SimpleNamespace(content=[], stop_reason="end_turn")
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk, model="claude-sonnet-5")

    client.create(system=[{"type": "text", "text": "sys"}], messages=[{"role": "user", "content": []}], tools=[{"name": "read_file"}])

    assert fake_sdk.last_call["model"] == "claude-sonnet-5"
    assert fake_sdk.last_call["system"] == [{"type": "text", "text": "sys"}]
    assert fake_sdk.last_call["tools"] == [{"name": "read_file"}]


def test_default_max_tokens_gives_headroom_for_a_long_turn():
    sdk_response = SimpleNamespace(content=[], stop_reason="end_turn")
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk)

    client.create(system=[], messages=[], tools=[])

    assert fake_sdk.last_call["max_tokens"] == DEFAULT_MAX_TOKENS


def test_max_tokens_is_configurable():
    sdk_response = SimpleNamespace(content=[], stop_reason="end_turn")
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk, max_tokens=32_000)

    client.create(system=[], messages=[], tools=[])

    assert fake_sdk.last_call["max_tokens"] == 32_000


def test_marks_end_of_message_history_as_a_cache_breakpoint():
    sdk_response = SimpleNamespace(content=[], stop_reason="end_turn")
    fake_sdk = FakeSDKClient(sdk_response)
    client = AnthropicModelClient(client=fake_sdk)
    original_messages = [
        {"role": "user", "content": [{"type": "text", "text": "first"}]},
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "c1", "content": "ok"},
                {"type": "tool_result", "tool_use_id": "c2", "content": "ok too"},
            ],
        },
    ]

    client.create(system=[], messages=original_messages, tools=[])

    sent_messages = fake_sdk.last_call["messages"]
    # only the last block of the last message is marked
    assert "cache_control" not in sent_messages[0]["content"][0]
    assert "cache_control" not in sent_messages[1]["content"][0]
    assert sent_messages[1]["content"][1]["cache_control"] == {"type": "ephemeral"}
    # the caller's own list/dicts (and the transcript entries backing them)
    # are never mutated
    assert "cache_control" not in original_messages[1]["content"][1]
