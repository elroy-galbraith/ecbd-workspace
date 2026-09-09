from types import SimpleNamespace

from app.model_client import AnthropicModelClient, TextBlock, ToolUseBlock


class FakeSDKClient:
    """Stands in for anthropic.Anthropic -- only the .messages.create shape
    that AnthropicModelClient depends on."""

    def __init__(self, sdk_response):
        self._response = sdk_response
        self.messages = SimpleNamespace(create=self._create)
        self.last_call = None

    def _create(self, **kwargs):
        self.last_call = kwargs
        return self._response


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
