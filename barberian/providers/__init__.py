"""Provider discovery, health and routing primitives."""

from dataclasses import dataclass
from time import monotonic


@dataclass(slots=True)
class ProviderSpec:
    name: str
    capability: str
    pricing: str = "unknown"
    model: str | None = None
    priority: int = 100


@dataclass(slots=True)
class ProviderHealth:
    healthy: bool = False
    latency_ms: int = 0
    checked_at: float = 0.0


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderSpec] = {}
        self._health: dict[str, ProviderHealth] = {}

    def register(self, spec: ProviderSpec) -> None:
        self._providers[spec.name] = spec
        self._health.setdefault(spec.name, ProviderHealth())

    def set_health(self, name: str, *, healthy: bool, latency_ms: int) -> None:
        if name not in self._providers:
            raise KeyError(name)
        self._health[name] = ProviderHealth(
            healthy=healthy,
            latency_ms=max(0, int(latency_ms)),
            checked_at=monotonic(),
        )

    def rank(self, capability: str, *, policy: str = "balanced") -> list[ProviderSpec]:
        candidates = [
            spec
            for spec in self._providers.values()
            if spec.capability == capability and self._health.get(spec.name, ProviderHealth()).healthy
        ]

        def key(spec: ProviderSpec) -> tuple:
            health = self._health[spec.name]
            free_rank = 0 if spec.pricing == "free" else 1
            if policy == "free_first":
                return (free_rank, spec.priority, health.latency_ms, spec.name)
            if policy == "fastest":
                return (health.latency_ms, spec.priority, free_rank, spec.name)
            if policy == "quality_first":
                return (spec.priority, health.latency_ms, free_rank, spec.name)
            return (spec.priority, health.latency_ms, free_rank, spec.name)

        return sorted(candidates, key=key)

    def snapshot(self) -> list[dict]:
        return [
            {
                "name": spec.name,
                "capability": spec.capability,
                "pricing": spec.pricing,
                "model": spec.model,
                "priority": spec.priority,
                "healthy": self._health[name].healthy,
                "latency_ms": self._health[name].latency_ms,
            }
            for name, spec in sorted(self._providers.items())
        ]
