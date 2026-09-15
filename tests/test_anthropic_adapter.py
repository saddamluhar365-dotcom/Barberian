from barberian.anthropic_adapter import AnthropicAdapter


def test_anthropic_payload_shape():
    adapter = AnthropicAdapter("x", "claude-test")
    payload = adapter.build_payload({"input": "hello"})
    assert payload["model"] == "claude-test"
    assert payload["messages"][0]["content"] == "hello"
