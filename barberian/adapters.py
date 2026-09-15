"""Stable provider adapter contract used by every external integration."""

from dataclasses import dataclass, field
from time import monotonic
from typing import Any, Iterator, Mapping

from .providers import ProviderErrorClass


@dataclass(slots=True)
class ProviderResponse:
    data: Any
    provider: str | None = None
    model: str | None = None
    latency_ms: int = 0
    raw: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "data": self.data,
            "provider": self.provider,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "metadata": dict(self.metadata),
        }


class ProviderAdapter:
    """Base contract; concrete adapters must implement execute/health as needed."""

    name = "generic"

    def discover(self) -> Mapping[str, Any]:
        return {"name": self.name}

    def health_check(self) -> ProviderResponse:
        return ProviderResponse(data={"healthy": False}, provider=self.name)

    def capabilities(self) -> list[str]:
        return []

    def models(self) -> list[str]:
        return []

    def execute(self, request: Mapping[str, Any]) -> ProviderResponse:
        raise NotImplementedError

    def stream(self, request: Mapping[str, Any]) -> Iterator[ProviderResponse]:
        response = self.execute(request)
        yield response

    def normalize_response(self, response: Any) -> ProviderResponse:
        return ProviderResponse(data=response, provider=self.name)

    def classify_error(self, error: BaseException) -> ProviderErrorClass:
        text = str(error).lower()
        if "timeout" in text:
            return ProviderErrorClass.TIMEOUT
        if "429" in text or "rate limit" in text:
            return ProviderErrorClass.RATE_LIMIT
        if "quota" in text:
            return ProviderErrorClass.QUOTA
        if "401" in text or "403" in text or "auth" in text:
            return ProviderErrorClass.AUTH
        if "500" in text or "502" in text or "503" in text:
            return ProviderErrorClass.SERVER_ERROR
        if "network" in text or "connection" in text:
            return ProviderErrorClass.NETWORK
        return ProviderErrorClass.UNKNOWN

    def quota_status(self) -> dict[str, Any]:
        return {"known": False}

    @staticmethod
    def timed(callable_, *args, **kwargs):
        started = monotonic()
        result = callable_(*args, **kwargs)
        return result, round((monotonic() - started) * 1000)
