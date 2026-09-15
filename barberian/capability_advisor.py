"""Capability-gap analysis and approved provider recommendations."""

from dataclasses import dataclass

from .capabilities import CapabilityRegistry
from .provider_catalog import CATALOG


@dataclass(slots=True, frozen=True)
class CapabilityAssessment:
    requested: tuple[str, ...]
    available: tuple[str, ...]
    missing: tuple[str, ...]
    unknown: tuple[str, ...]
    suggestions: dict[str, tuple[str, ...]]


class CapabilityAdvisor:
    def __init__(self, registry: CapabilityRegistry | None = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def assess(self, capabilities: list[str] | tuple[str, ...]) -> CapabilityAssessment:
        requested = tuple(dict.fromkeys(item.strip().lower() for item in capabilities if item.strip()))
        known = {item.name for item in self.registry.list()}
        available = tuple(item for item in requested if item in known)
        unknown = tuple(item for item in requested if item not in known)
        catalog_caps: dict[str, list[str]] = {}
        for entry in CATALOG.values():
            catalog_caps.setdefault(entry.capability, []).append(entry.name)
        missing = tuple(item for item in available if not any(e.capability == item for e in CATALOG.values()))
        suggestions = {item: tuple(sorted(catalog_caps.get(item, ()))) for item in requested if catalog_caps.get(item)}
        return CapabilityAssessment(requested, available, missing, unknown, suggestions)
