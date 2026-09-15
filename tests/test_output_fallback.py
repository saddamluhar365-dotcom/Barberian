from barberian.adapters import ProviderAdapter, ProviderResponse
from barberian.providers import ProviderRegistry, ProviderSpec
from barberian.routing import SmartRouter
from barberian.services import ProviderExecutor


class EmptyAdapter(ProviderAdapter):
    name = "empty"
    def execute(self, request):
        return ProviderResponse(data="", provider=self.name)


class GoodAdapter(ProviderAdapter):
    name = "good"
    def execute(self, request):
        return ProviderResponse(data="valid", provider=self.name)


def test_invalid_empty_output_triggers_fallback():
    registry = ProviderRegistry()
    registry.register(ProviderSpec("empty", "llm", priority=1))
    registry.register(ProviderSpec("good", "llm", priority=2))
    registry.set_health("empty", healthy=True, latency_ms=1)
    registry.set_health("good", healthy=True, latency_ms=2)
    result = ProviderExecutor(SmartRouter(registry), {"empty": EmptyAdapter(), "good": GoodAdapter()}).execute("llm", {"input": "x"})
    assert result.provider == "good"
    assert result.attempts == ["empty", "good"]
