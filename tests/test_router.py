from barberian.providers import ProviderRegistry, ProviderSpec, ProviderStatus
from barberian.routing import SmartRouter


def test_router_returns_primary_and_fallback_chain():
    registry = ProviderRegistry()
    for name, priority in (("a", 10), ("b", 20), ("c", 30)):
        registry.register(ProviderSpec(name, "llm", pricing="free", priority=priority))
        registry.set_health(name, healthy=True, latency_ms=priority, status=ProviderStatus.ACTIVE)
    router = SmartRouter(registry)
    route = router.select("llm", policy="free_first")
    assert route.primary.name == "a"
    assert [p.name for p in route.fallbacks] == ["b", "c"]


def test_router_excludes_disabled_or_unhealthy():
    registry = ProviderRegistry()
    registry.register(ProviderSpec("bad", "llm"))
    registry.set_health("bad", healthy=False, latency_ms=0, status=ProviderStatus.AUTH_ERROR)
    router = SmartRouter(registry)
    assert router.select("llm").primary is None
