from barberian.providers import discover_environment_providers


def test_custom_provider_discovery_supports_unlimited_named_slots():
    env = {
        "BARBERIAN_PROVIDER_ALPHA_KEY": "secret-a",
        "BARBERIAN_PROVIDER_ALPHA_ENDPOINT": "https://example.test/a",
        "BARBERIAN_PROVIDER_ALPHA_CAPABILITY": "llm",
        "BARBERIAN_PROVIDER_BETA_KEY": "secret-b",
        "BARBERIAN_PROVIDER_BETA_ENDPOINT": "https://example.test/b",
        "BARBERIAN_PROVIDER_BETA_CAPABILITY": "search",
    }
    found = discover_environment_providers(env)
    assert {item.name for item in found} == {"alpha", "beta"}
    assert all(item.env_key.endswith("_KEY") for item in found)
