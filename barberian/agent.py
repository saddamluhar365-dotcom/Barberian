"""Top-level agent facade: intent classification, capability discovery and commands."""

import re
from typing import Any

from . import registry
from .config import Settings
from .providers import ProviderRegistry, ProviderSpec, discover_environment_providers


class Agent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.providers = ProviderRegistry()
        self.refresh_providers()

    def refresh_providers(self) -> list[dict[str, Any]]:
        discovered = discover_environment_providers()
        for candidate in discovered:
            self.providers.register(
                ProviderSpec(
                    name=candidate.name,
                    capability=candidate.capability,
                    pricing=candidate.pricing,
                    env_key=candidate.env_key,
                )
            )
        return self.providers.snapshot()

    def status(self) -> dict[str, Any]:
        return {"ok": True, "service": "barberian", "providers": self.providers.snapshot()}

    def handle(self, message: str) -> dict[str, Any]:
        text = message.strip()
        if not text:
            return {"ok": False, "error": "message is required"}
        lowered = text.lower()

        match = re.fullmatch(r"add\s+(.+?)\s+(mcp|skill)", lowered)
        if match:
            name, kind = match.groups()
            return registry.add(kind, name)
        match = re.fullmatch(r"(?:list|show)\s+(mcp|skills?)", lowered)
        if match:
            kind = "skill" if match.group(1).startswith("skill") else "mcp"
            return registry.list_items(kind)
        match = re.fullmatch(r"disable\s+(.+?)\s+(mcp|skill)", lowered)
        if match:
            name, kind = match.groups()
            return registry.disable(kind, name)
        if lowered in {"api", "apis", "list apis", "show apis", "api status"}:
            self.refresh_providers()
            return {"ok": True, "type": "providers", "items": self.providers.snapshot()}
        if lowered in {"status", "health", "system status"}:
            return self.status()
        return {
            "ok": True,
            "type": "chat",
            "message": "Request accepted. Capability discovery and execution are ready; add/configure a compatible provider for external execution.",
            "providers": self.providers.snapshot(),
        }


_default_agent = Agent()


def handle_message(message: str) -> dict[str, Any]:
    return _default_agent.handle(message)
