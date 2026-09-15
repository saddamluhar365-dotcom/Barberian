"""Top-level universal agent runtime."""

import re
from typing import Any

from . import registry
from .adapters import ProviderAdapter
from .capabilities import CapabilityRegistry
from .capability_advisor import CapabilityAdvisor
from .config import Settings
from .http_providers import OpenAICompatibleAdapter
from .provider_manager import ProviderManager
from .providers import ProviderRegistry, ProviderSpec, ProviderStatus
from .routing import SmartRouter
from .services import ProviderExecutor


class Agent:
    """Coordinates capability discovery, routing, execution, verification and commands."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.providers = ProviderRegistry()
        self.manager = ProviderManager(registry=self.providers)
        self.adapters: dict[str, ProviderAdapter] = {}
        self.router = SmartRouter(self.providers)
        self.capabilities = CapabilityRegistry()
        self.refresh_providers()

    def refresh_providers(self) -> list[dict[str, Any]]:
        self.manager.discover()
        self._build_adapters()
        return self.providers.snapshot()

    def _build_adapters(self) -> None:
        for spec in list(self.providers._providers.values()):
            if spec.name in self.adapters:
                continue
            key = spec.env_key
            secret = self.manager.environment.get(key) if key else None
            if not secret or not spec.endpoint or not spec.model:
                continue
            catalog_adapter = self.manager.adapter_kind(spec.name)
            if catalog_adapter == "http":
                self.adapters[spec.name] = OpenAICompatibleAdapter(
                    secret, spec.endpoint, spec.model, name=spec.name, timeout=self.settings.request_timeout_seconds
                )

    def check_providers(self) -> list[dict[str, Any]]:
        """Run a real minimal provider request for configured executable providers."""
        self.refresh_providers()
        results: list[dict[str, Any]] = []
        for spec in self.providers._providers.values():
            adapter = self.adapters.get(spec.name)
            if adapter is None:
                results.append({"name": spec.name, "status": ProviderStatus.UNKNOWN.value, "healthy": False, "message": "adapter unavailable"})
                continue
            try:
                response, latency = adapter.timed(adapter.execute, {"input": "Reply with OK.", "max_tokens": 1})
                valid = response is not None
                self.providers.set_health(spec.name, healthy=valid, latency_ms=latency, status=ProviderStatus.ACTIVE if valid else ProviderStatus.DEGRADED)
                results.append({"name": spec.name, "status": ProviderStatus.ACTIVE.value if valid else ProviderStatus.DEGRADED.value, "healthy": valid, "latency_ms": latency})
            except Exception as exc:
                kind = adapter.classify_error(exc)
                status = {
                    "rate_limit": ProviderStatus.RATE_LIMITED,
                    "quota": ProviderStatus.QUOTA_LOW,
                    "auth": ProviderStatus.AUTH_ERROR,
                    "timeout": ProviderStatus.DOWN,
                    "server_error": ProviderStatus.DEGRADED,
                }.get(kind.value, ProviderStatus.DOWN)
                self.providers.set_health(spec.name, healthy=False, latency_ms=0, status=status, message=str(exc))
                results.append({"name": spec.name, "status": status.value, "healthy": False, "message": str(exc)})
        return results

    def execute(self, message: str, *, capability: str = "llm", policy: str | None = None) -> dict[str, Any]:
        text = message.strip()
        if not text:
            return {"ok": False, "error": "message is required"}
        self.refresh_providers()
        # A configured approved adapter is eligible before its first explicit probe; failures then update the breaker.
        for spec in self.providers._providers.values():
            if spec.name in self.adapters and not self.providers._health[spec.name].healthy:
                self.providers.set_health(spec.name, healthy=True, latency_ms=0, status=ProviderStatus.ACTIVE)
        executor = ProviderExecutor(self.router, self.adapters, self.providers)
        result = executor.execute(capability, {"input": text}, policy=policy or self.settings.routing_policy)
        data = result.data
        if isinstance(data, dict):
            choices = data.get("choices")
            if choices and isinstance(choices, list):
                message_obj = choices[0].get("message", {})
                if isinstance(message_obj, dict) and message_obj.get("content") is not None:
                    data = message_obj["content"]
        return {"ok": True, "type": "execution", "data": data, "provider": result.provider, "model": result.model, "latency_ms": result.latency_ms, "attempts": result.attempts, "errors": result.errors}

    def capability_status(self) -> dict[str, Any]:
        configured = {spec.capability for spec in self.providers._providers.values() if spec.name in self.adapters}
        assessment = CapabilityAdvisor(self.capabilities, configured).assess([item.name for item in self.capabilities.list()])
        return {"missing": list(assessment.missing), "unknown": list(assessment.unknown), "suggestions": {k: list(v) for k, v in assessment.suggestions.items()}}

    def status(self) -> dict[str, Any]:
        return {"ok": True, "service": "barberian", "version": "0.3.0", "routing_policy": self.settings.routing_policy, "providers": self.providers.snapshot(), "adapters": sorted(self.adapters), "capability_gaps": self.capability_status()}

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
            return {"ok": True, "type": "providers", "items": self.refresh_providers()}
        if lowered in {"check api", "check apis", "check providers", "health check"}:
            return {"ok": True, "type": "provider_health", "items": self.check_providers()}
        if lowered in {"capabilities", "list capabilities", "missing capabilities"}:
            return {"ok": True, "type": "capabilities", **self.capability_status()}
        if lowered in {"status", "health", "system status"}:
            return self.status()
        if lowered.startswith("research "):
            return {"ok": True, "type": "research", "message": "Research workflow is registered; configure a search provider to execute it."}
        try:
            return self.execute(text)
        except RuntimeError as exc:
            return {"ok": False, "type": "execution", "error": str(exc), "providers": self.providers.snapshot()}


_default_agent = Agent()


def handle_message(message: str) -> dict[str, Any]:
    return _default_agent.handle(message)
