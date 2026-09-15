from barberian.http_providers import OpenAICompatibleAdapter


def test_openai_compatible_request_shape_is_normalized():
    adapter = OpenAICompatibleAdapter(api_key="x", endpoint="https://example.test/v1/chat/completions", model="demo")
    payload = adapter.build_payload({"input": "hello"})
    assert payload["model"] == "demo"
    assert payload["messages"][0]["content"] == "hello"
    assert "api_key" not in payload
