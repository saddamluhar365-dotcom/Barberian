"""Bridge environment discovery to the approved provider catalog and registry."""

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
            if catalog is None or not self.environment.get(catalog.key_env):
                continue
            spec = ProviderSpec(
                name=catalog.name,
                capability=catalog.capability,
                pricing="unknown",
                model=self.environment.get(catalog.model_env or "") or catalog.default_model,
                endpoint=self.environment.get(catalog.endpoint_env or "") or catalog.default_endpoint,
                env_key=catalog.key_env,
            )
            self.registry.register(spec)
            result.append(spec)
        return result

    def snapshot(self) -> list[dict]:
        return self.registry.snapshot()
