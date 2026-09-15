from barberian.providers import ProviderRegistry, ProviderSpec


def test_register_and_rank_healthy_providers():
    registry = ProviderRegistry()
    registry.register(ProviderSpec("fast-ai", "llm", "free", priority=20))
    registry.register(ProviderSpec("quality-ai", "llm", "paid", priority=10))
    registry.set_health("fast-ai", healthy=True, latency_ms=80)
    registry.set_health("quality-ai", healthy=True, latency_ms=140)

    ranked = registry.rank("llm", policy="free_first")

    assert [item.name for item in ranked] == ["fast-ai", "quality-ai"]


def test_unhealthy_provider_is_excluded():
    registry = ProviderRegistry()
    registry.register(ProviderSpec("broken", "llm", "free"))
    registry.set_health("broken", healthy=False, latency_ms=0)

    assert registry.rank("llm", policy="free_first") == []
