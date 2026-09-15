"""Capability-gap analysis and approved provider recommendations."""

from dataclasses import dataclass

from .capabilities import CapabilityRegistry
from .provider_catalog import CATALOG


RECOMMENDATIONS = {
    "llm": ("openrouter", "groq", "mistral"),
    "search": ("tavily", "serper", "perplexity"),
    "image": ("replicate",),
    "video": ("runway",),
    "audio": ("elevenlabs",),
    "code": ("openrouter", "groq"),
    "research": ("tavily", "perplexity"),
}


@dataclass(slots=True, frozen=True)
class CapabilityAssessment:
    requested: tuple[str, ...]
    available: tuple[str, ...]
    missing: tuple[str, ...]
    unknown: tuple[str, ...]
    suggestions: dict[str, tuple[str, ...]]


class CapabilityAdvisor:
    def __init__(self, registry: CapabilityRegistry | None = None, configured: set[str] | None = None) -> None:
        self.registry = registry or CapabilityRegistry()
        self.configured = configured or set()

    def assess(self, capabilities: list[str] | tuple[str, ...]) -> CapabilityAssessment:
        requested = tuple(dict.fromkeys(item.strip().lower() for item in capabilities if item.strip()))
        known = {item.name for item in self.registry.list()}
        available = tuple(item for item in requested if item in known and item in self.configured)
        unknown = tuple(item for item in requested if item not in known)
        missing = tuple(item for item in requested if item in known and item not in self.configured)
        suggestions = {
            item: tuple(provider for provider in RECOMMENDATIONS.get(item, ()) if provider in CATALOG)
            for item in missing
            if RECOMMENDATIONS.get(item)
        }
        return CapabilityAssessment(requested, available, missing, unknown, suggestions)
