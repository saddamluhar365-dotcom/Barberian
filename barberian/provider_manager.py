"""Bridge environment discovery to the approved catalog and explicit custom providers."""

import os
from typing import Mapping

from .provider_catalog import get
from .providers import ProviderRegistry, ProviderSpec, discover_environment_providers


class ProviderManager:
    def __init__(self, environment: Mapping[str, str] | None = None, registry: ProviderRegistry | None = None) -> None:
        self.environment = os.environ if environment is None else environment
        self.registry = registry or ProviderRegistry()

    def discover(self) -> list[ProviderSpec]:
        result: list[ProviderSpec] = []
        for candidate in discover_environment_providers(self.environment):
            catalog = get(candidate.name)
            if catalog is not None:
                spec = ProviderSpec(catalog.name, catalog.capability, self.environment.get(f"{candidate.name.upper()}_PRICING", candidate.pricing), self.environment.get(catalog.model_env or "") or catalog.default_model, int(self.environment.get(f"{candidate.name.upper()}_PRIORITY", "100")), self.environment.get(catalog.endpoint_env or "") or catalog.default_endpoint, catalog.key_env, {"adapter": catalog.adapter, "confidence": candidate.confidence})
            else:
                prefix = f"BARBERIAN_PROVIDER_{candidate.name.upper()}_"
                spec = ProviderSpec(candidate.name, candidate.capability, candidate.pricing, candidate.model, int(self.environment.get(f"{prefix}PRIORITY", "100")), candidate.endpoint, candidate.env_key, {"adapter": candidate.adapter, "confidence": candidate.confidence})
            self.registry.register(spec)
            result.append(spec)
        return result

    def adapter_kind(self, name: str) -> str | None:
        entry = get(name)
        if entry:
            return entry.adapter
        return self.registry.get(name).metadata.get("adapter") if self.registry.get(name) else None

    def snapshot(self) -> list[dict]:
        return self.registry.snapshot()
