from barberian.search_adapters import TavilyAdapter, SerperAdapter


def test_tavily_payload_contains_query_without_secret():
    adapter = TavilyAdapter("secret")
    payload = adapter.build_payload({"query": "latest AI news"})
    assert payload["query"] == "latest AI news"
    assert "api_key" not in payload


def test_serper_payload_contains_query_without_secret():
    adapter = SerperAdapter("secret")
    payload = adapter.build_payload({"query": "python"})
    assert payload == {"q": "python"}
