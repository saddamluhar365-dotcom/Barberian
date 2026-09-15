import os

import pytest

from barberian.providers import (
    CircuitBreaker,
    ProviderErrorClass,
    ProviderRegistry,
    ProviderSpec,
    ProviderStatus,
    discover_environment_providers,
)


def test_environment_discovery_uses_key_name_and_never_exposes_secret(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-value")
    monkeypatch.setenv("GEMINI_API_KEY", "another-secret")
    monkeypatch.setenv("UNRELATED_VALUE", "safe")

    found = discover_environment_providers(os.environ)

    names = {item.name for item in found}
    assert "openai" in names
    assert "gemini" in names
    assert all("secret" not in repr(item).lower() for item in found)


def test_registry_routes_by_capability_and_policy():
    registry = ProviderRegistry()
    registry.register(ProviderSpec("slow-free", "llm", pricing="free", priority=50))
    registry.register(ProviderSpec("fast-paid", "llm", pricing="paid", priority=10))
    registry.set_health("slow-free", healthy=True, latency_ms=200)
    registry.set_health("fast-paid", healthy=True, latency_ms=50)

    assert registry.rank("llm", policy="free_first")[0].name == "slow-free"
    assert registry.rank("llm", policy="fastest")[0].name == "fast-paid"


def test_circuit_breaker_opens_after_failures_and_recovers():
    breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    assert breaker.allow() is True
    breaker.record_failure(ProviderErrorClass.TIMEOUT)
    breaker.record_failure(ProviderErrorClass.SERVER_ERROR)
    assert breaker.allow() is False
    breaker.force_half_open()
    assert breaker.allow() is True
    breaker.record_success()
    assert breaker.allow() is True


def test_provider_status_values_are_stable():
    assert ProviderStatus.ACTIVE.value == "ACTIVE"
    assert ProviderStatus.AUTH_ERROR.value == "AUTH_ERROR"
