"""Policy-aware provider selection and fallback-chain construction."""

from dataclasses import dataclass

from .providers import ProviderRegistry, ProviderSpec


@dataclass(slots=True, frozen=True)
class Route:
    primary: ProviderSpec | None
    fallbacks: list[ProviderSpec]
    policy: str
    capability: str


class SmartRouter:
    VALID_POLICIES = {"free_first", "fastest", "quality_first", "balanced"}

    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    def select(self, capability: str, *, policy: str = "balanced", limit: int = 5) -> Route:
        normalized = policy.strip().lower()
        if normalized not in self.VALID_POLICIES:
            raise ValueError(f"unsupported routing policy: {policy}")
        if limit < 1:
            raise ValueError("limit must be >= 1")
        ranked = self.registry.rank(capability, policy=normalized)
        return Route(
            primary=ranked[0] if ranked else None,
            fallbacks=ranked[1:limit],
            policy=normalized,
            capability=capability.strip().lower(),
        )
