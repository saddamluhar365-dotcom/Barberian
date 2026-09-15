from barberian.agent import Agent
from barberian.config import Settings


class FakeAdapter:
    def __init__(self, name):
        self.name = name

    def execute(self, request):
        from barberian.adapters import ProviderResponse
        return ProviderResponse(data=f"answer:{request['input']}", provider=self.name, model="fake")

    def classify_error(self, error):
        from barberian.providers import ProviderErrorClass
        return ProviderErrorClass.UNKNOWN

    @staticmethod
    def timed(callable_, *args, **kwargs):
        return callable_(*args, **kwargs), 1


def test_agent_executes_llm_request_through_router():
    agent = Agent(Settings(routing_policy="free_first"))
    agent.providers.register(__import__('barberian.providers', fromlist=['ProviderSpec']).ProviderSpec("fake", "llm", pricing="free", priority=1))
    agent.providers.set_health("fake", healthy=True, latency_ms=1)
    agent.adapters = {"fake": FakeAdapter("fake")}
    result = agent.execute("hello")
    assert result["ok"] is True
    assert result["provider"] == "fake"
    assert result["data"] == "answer:hello"
