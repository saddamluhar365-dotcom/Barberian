from barberian.provider_catalog import get
from barberian.provider_manager import ProviderManager


def test_gemini_catalog_entry():
    entry = get("gemini")
    assert entry is not None
    assert entry.capability == "llm"
    assert entry.key_env == "GEMINI_API_KEY"
    assert entry.model_env == "GEMINI_MODEL"
    assert entry.default_model == "gemini-2.5-flash"
    assert entry.default_endpoint.endswith("/v1beta/openai/chat/completions")


def test_gemini_is_discovered_from_render_environment():
    manager = ProviderManager(environment={"GEMINI_API_KEY": "test-key"})
    providers = manager.discover()
    gemini = next(item for item in providers if item.name == "gemini")
    assert gemini.capability == "llm"
    assert gemini.env_key == "GEMINI_API_KEY"
    assert gemini.model == "gemini-2.5-flash"
    assert gemini.endpoint == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
