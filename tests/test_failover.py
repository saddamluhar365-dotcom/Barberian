from barberian.adapters import ProviderAdapter, ProviderResponse
from barberian.providers import ProviderRegistry, ProviderSpec
from barberian.routing import SmartRouter
from barberian.services import ProviderExecutor


class FailingAdapter(ProviderAdapter):
    name = "first"
    def execute(self, request):
        raise TimeoutError("timeout")


class WorkingAdapter(ProviderAdapter):
    name = "second"
    def execute(self, request):
        return ProviderResponse(data="done", provider=self.name)


def test_executor_fails_over_without_losing_request():
    registry = ProviderRegistry()
    registry.register(ProviderSpec("first", "llm", priority=1))
    registry.register(ProviderSpec("second", "llm", priority=2))
    registry.set_health("first", healthy=True, latency_ms=10)
    registry.set_health("second", healthy=True, latency_ms=20)
    router = SmartRouter(registry)
    executor = ProviderExecutor(router, {"first": FailingAdapter(), "second": WorkingAdapter()})

    result = executor.execute("llm", {"input": "keep this"})

    assert result.data == "done"
    assert result.provider == "second"
    assert result.attempts == ["first", "second"]
