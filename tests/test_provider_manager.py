from barberian.provider_catalog import get
from barberian.provider_manager import ProviderManager


def test_catalog_resolves_approved_provider():
    item = get("openai")
    assert item is not None
    assert item.key_env == "OPENAI_API_KEY"
    assert item.capability == "llm"


def test_manager_does_not_report_unknown_keys_as_approved():
    manager = ProviderManager(environment={"UNKNOWN_API_KEY": "x"})
    assert manager.discover() == []
