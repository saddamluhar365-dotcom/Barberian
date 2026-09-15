"""Provider discovery, health, routing and failure-control primitives."""

from dataclasses import dataclass, field
from enum import Enum
import os
from time import monotonic
from typing import Mapping


class ProviderStatus(str, Enum):
    ACTIVE = "ACTIVE"
    STANDBY = "STANDBY"
    DEGRADED = "DEGRADED"
    RATE_LIMITED = "RATE_LIMITED"
    QUOTA_LOW = "QUOTA_LOW"
    AUTH_ERROR = "AUTH_ERROR"
    DOWN = "DOWN"
    DISABLED = "DISABLED"
    UNKNOWN = "UNKNOWN"


class ProviderErrorClass(str, Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    QUOTA = "quota"
    AUTH = "auth"
    SERVER_ERROR = "server_error"
    INVALID_OUTPUT = "invalid_output"
    NETWORK = "network"
    UNKNOWN = "unknown"


@dataclass(slots=True, frozen=True)
class ProviderSpec:
    name: str
    capability: str
    pricing: str = "unknown"
    model: str | None = None
    priority: int = 100
    endpoint: str | None = None
    env_key: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(slots=True)
class ProviderHealth:
    healthy: bool = False
    latency_ms: int = 0
    checked_at: float = 0.0
    status: ProviderStatus = ProviderStatus.UNKNOWN
    message: str = ""


@dataclass(slots=True, frozen=True)
class ProviderCandidate:
    name: str
    capability: str
    env_key: str
    pricing: str = "unknown"
    model: str | None = None
    confidence: float = 0.0


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 30.0) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failures = 0
        self.opened_at = 0.0
        self.half_open = False

    def allow(self) -> bool:
        if self.opened_at == 0.0:
            return True
        if self.half_open:
            return True
        if monotonic() - self.opened_at >= self.cooldown_seconds:
            self.half_open = True
            return True
        return False

    def record_failure(self, error: ProviderErrorClass = ProviderErrorClass.UNKNOWN) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = monotonic()
            self.half_open = False

    def record_success(self) -> None:
        self.failures = 0
        self.opened_at = 0.0
        self.half_open = False

    def force_half_open(self) -> None:
        if self.opened_at == 0.0:
            self.opened_at = monotonic()
        self.half_open = True


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ProviderSpec] = {}
        self._health: dict[str, ProviderHealth] = {}
        self._breakers: dict[str, CircuitBreaker] = {}

    def register(self, spec: ProviderSpec) -> None:
        key = spec.name.strip().lower()
        if not key:
            raise ValueError("provider name is required")
        normalized = ProviderSpec(
            name=key,
            capability=spec.capability.strip().lower(),
            pricing=spec.pricing.strip().lower(),
            model=spec.model,
            priority=int(spec.priority),
            endpoint=spec.endpoint,
            env_key=spec.env_key,
            metadata=dict(spec.metadata),
        )
        self._providers[key] = normalized
        self._health.setdefault(key, ProviderHealth())
        self._breakers.setdefault(key, CircuitBreaker())

    def set_health(
        self,
        name: str,
        *,
        healthy: bool,
        latency_ms: int,
        status: ProviderStatus | None = None,
        message: str = "",
    ) -> None:
        key = name.strip().lower()
        if key not in self._providers:
            raise KeyError(name)
        resolved_status = status or (ProviderStatus.ACTIVE if healthy else ProviderStatus.DOWN)
        self._health[key] = ProviderHealth(
            healthy=healthy,
            latency_ms=max(0, int(latency_ms)),
            checked_at=monotonic(),
            status=resolved_status,
            message=message,
        )

    def breaker(self, name: str) -> CircuitBreaker:
        return self._breakers[name.strip().lower()]

    def get(self, name: str) -> ProviderSpec | None:
        return self._providers.get(name.strip().lower())

    def rank(self, capability: str, *, policy: str = "balanced") -> list[ProviderSpec]:
        capability = capability.strip().lower()
        candidates = []
        for spec in self._providers.values():
            health = self._health.get(spec.name, ProviderHealth())
            breaker = self._breakers.get(spec.name)
            if spec.capability != capability or not health.healthy:
                continue
            if breaker is not None and not breaker.allow():
                continue
            candidates.append(spec)

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
                "endpoint": spec.endpoint,
                "env_key": spec.env_key,
                "healthy": self._health[name].healthy,
                "status": self._health[name].status.value,
                "latency_ms": self._health[name].latency_ms,
            }
            for name, spec in sorted(self._providers.items())
        ]


_PROVIDER_ENV_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("OPENAI_API_KEY", "openai", "llm", "unknown"),
    ("GEMINI_API_KEY", "gemini", "llm", "unknown"),
    ("ANTHROPIC_API_KEY", "anthropic", "llm", "unknown"),
    ("GROQ_API_KEY", "groq", "llm", "unknown"),
    ("MISTRAL_API_KEY", "mistral", "llm", "unknown"),
    ("COHERE_API_KEY", "cohere", "llm", "unknown"),
    ("OPENROUTER_API_KEY", "openrouter", "llm", "unknown"),
    ("PERPLEXITY_API_KEY", "perplexity", "search", "unknown"),
    ("TAVILY_API_KEY", "tavily", "search", "unknown"),
    ("SERPER_API_KEY", "serper", "search", "unknown"),
    ("REPLICATE_API_TOKEN", "replicate", "image", "unknown"),
    ("RUNWAY_API_KEY", "runway", "video", "unknown"),
    ("ELEVENLABS_API_KEY", "elevenlabs", "audio", "unknown"),
)


def discover_environment_providers(environment: Mapping[str, str] | None = None) -> list[ProviderCandidate]:
    """Discover known provider credentials without returning their secret values."""
    env = os.environ if environment is None else environment
    found: list[ProviderCandidate] = []
    for key, name, capability, pricing in _PROVIDER_ENV_RULES:
        if env.get(key):
            found.append(
                ProviderCandidate(
                    name=name,
                    capability=capability,
                    env_key=key,
                    pricing=pricing,
                    confidence=1.0,
                )
            )
    return found


__all__ = [
    "CircuitBreaker",
    "ProviderCandidate",
    "ProviderErrorClass",
    "ProviderHealth",
    "ProviderRegistry",
    "ProviderSpec",
    "ProviderStatus",
    "discover_environment_providers",
]
