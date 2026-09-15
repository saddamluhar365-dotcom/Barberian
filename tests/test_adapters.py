import pytest

from barberian.adapters import ProviderAdapter, ProviderResponse


def test_provider_adapter_contract_is_explicit():
    adapter = ProviderAdapter()
    assert adapter.capabilities() == []
    assert adapter.models() == []
    assert adapter.normalize_response({"ok": True}).data == {"ok": True}


def test_unconfigured_adapter_cannot_execute():
    with pytest.raises(NotImplementedError):
        ProviderAdapter().execute({"input": "hello"})


def test_response_normalization_has_metadata():
    response = ProviderResponse(data="x", provider="demo", model="m", latency_ms=12)
    assert response.to_dict()["provider"] == "demo"
    assert response.to_dict()["latency_ms"] == 12
