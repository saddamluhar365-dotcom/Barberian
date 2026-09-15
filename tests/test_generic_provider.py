from barberian.generic_provider import GenericJSONAdapter


def test_generic_json_adapter_keeps_request_schema_provider_neutral():
    adapter = GenericJSONAdapter("secret", "https://example.test/api", name="custom")
    payload = adapter.build_payload({"input": "hello", "query": "q"})
    assert payload == {"input": "hello", "query": "q"}
