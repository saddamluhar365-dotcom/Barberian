"""Provider execution with bounded failover, circuit-breaker feedback and telemetry."""

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .adapters import ProviderAdapter, ProviderResponse
from .providers import ProviderErrorClass, ProviderRegistry
from .routing import SmartRouter
from .usage import UsageTracker


@dataclass(slots=True)
class ExecutionResponse:
    data: Any
    provider: str | None
    model: str | None = None
    latency_ms: int = 0
    attempts: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderExecutor:
    def __init__(self, router: SmartRouter, adapters: Mapping[str, ProviderAdapter], registry: ProviderRegistry | None = None, usage: UsageTracker | None = None, validator: Callable[[Any], bool] | None = None) -> None:
        self.router = router
        self.adapters = {key.strip().lower(): value for key, value in adapters.items()}
        self.registry = registry or router.registry
        self.usage = usage or UsageTracker()
        self.validator = validator or self._default_valid

    @staticmethod
    def _default_valid(data: Any) -> bool:
        if data is None:
            return False
        if isinstance(data, str) and not data.strip():
            return False
        return True

    def execute(self, capability: str, request: Mapping[str, Any], *, policy: str = "balanced") -> ExecutionResponse:
        route = self.router.select(capability, policy=policy)
        candidates = ([route.primary] if route.primary else []) + route.fallbacks
        attempts: list[str] = []
        errors: dict[str, str] = {}
        for spec in candidates:
            adapter = self.adapters.get(spec.name)
            if adapter is None:
                errors[spec.name] = "adapter not configured"
                continue
            attempts.append(spec.name)
            try:
                response, latency = adapter.timed(adapter.execute, request)
                normalized = response if isinstance(response, ProviderResponse) else adapter.normalize_response(response)
                if not self.validator(normalized.data):
                    raise ValueError("provider returned invalid output")
                normalized.latency_ms = latency
                self.registry.breaker(spec.name).record_success()
                tokens = int(normalized.metadata.get("tokens", 0) or 0)
                self.usage.record(spec.name, tokens=tokens, latency_ms=latency, success=True)
                return ExecutionResponse(data=normalized.data, provider=normalized.provider or spec.name, model=normalized.model or spec.model, latency_ms=normalized.latency_ms, attempts=attempts, errors=errors, metadata=dict(normalized.metadata))
            except Exception as exc:
                errors[spec.name] = str(exc)
                error_class = adapter.classify_error(exc)
                if isinstance(exc, ValueError) and "invalid output" in str(exc).lower():
                    error_class = ProviderErrorClass.INVALID_OUTPUT
                self.registry.breaker(spec.name).record_failure(error_class)
                self.usage.record(spec.name, latency_ms=0, success=False)
        raise RuntimeError({"message": "all provider attempts failed", "attempts": attempts, "errors": errors})
