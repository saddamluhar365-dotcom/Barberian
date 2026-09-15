"""Top-level universal agent runtime."""

import re
from typing import Any

from . import __version__, registry
from .adapters import ProviderAdapter
from .anthropic_adapter import AnthropicAdapter
from .capabilities import CapabilityRegistry
from .capability_advisor import CapabilityAdvisor
from .config import Settings
from .generic_provider import GenericJSONAdapter
from .http_providers import OpenAICompatibleAdapter
from .intent import infer_capability
from .media_adapters import ElevenLabsAdapter, ReplicateAdapter, RunwayAdapter
from .provider_manager import ProviderManager
from .providers import ProviderRegistry, ProviderStatus
from .research import ResearchEngine, ResearchSource
from .routing import SmartRouter
from .search_adapters import SerperAdapter, TavilyAdapter
from .services import ProviderExecutor


class Agent:
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
            secret = self.manager.environment.get(spec.env_key) if spec.env_key else None
            if not secret or not spec.endpoint:
                continue
            kind = self.manager.adapter_kind(spec.name)
            if kind == "http" and spec.model:
                self.adapters[spec.name] = OpenAICompatibleAdapter(secret, spec.endpoint, spec.model, name=spec.name, timeout=self.settings.request_timeout_seconds)
            elif kind == "anthropic" and spec.model:
                self.adapters[spec.name] = AnthropicAdapter(secret, spec.model, spec.endpoint, self.settings.request_timeout_seconds)
            elif kind == "tavily":
                self.adapters[spec.name] = TavilyAdapter(secret, spec.endpoint)
            elif kind == "serper":
                self.adapters[spec.name] = SerperAdapter(secret, spec.endpoint)
            elif kind == "replicate" and spec.model:
                self.adapters[spec.name] = ReplicateAdapter(secret, spec.model, spec.endpoint)
            elif kind == "runway" and spec.model:
                self.adapters[spec.name] = RunwayAdapter(secret, spec.model, f"{spec.endpoint.rstrip('/')}/image_to_video")
            elif kind == "elevenlabs":
                voice_id = self.manager.environment.get("ELEVENLABS_VOICE_ID")
                if voice_id:
                    self.adapters[spec.name] = ElevenLabsAdapter(secret, voice_id, spec.endpoint)
            elif kind == "generic":
                self.adapters[spec.name] = GenericJSONAdapter(secret, spec.endpoint, name=spec.name, capability=spec.capability, timeout=self.settings.request_timeout_seconds)

    def check_providers(self) -> list[dict[str, Any]]:
        self.refresh_providers()
        results = []
        for spec in self.providers._providers.values():
            adapter = self.adapters.get(spec.name)
            if adapter is None:
                results.append({"name": spec.name, "status": ProviderStatus.UNKNOWN.value, "healthy": False, "message": "adapter unavailable"})
                continue
            try:
                probe = {"input": "Reply with OK.", "max_tokens": 1} if spec.capability == "llm" else {"query": "OpenAI"} if spec.capability == "search" else {"text": "OK"} if spec.capability == "audio" else {"prompt": "test"}
                response, latency = adapter.timed(adapter.execute, probe)
                valid = response is not None
                self.providers.set_health(spec.name, healthy=valid, latency_ms=latency, status=ProviderStatus.ACTIVE if valid else ProviderStatus.DEGRADED)
                results.append({"name": spec.name, "status": ProviderStatus.ACTIVE.value if valid else ProviderStatus.DEGRADED.value, "healthy": valid, "latency_ms": latency})
            except Exception as exc:
                kind = adapter.classify_error(exc)
                status = {"rate_limit": ProviderStatus.RATE_LIMITED, "quota": ProviderStatus.QUOTA_LOW, "auth": ProviderStatus.AUTH_ERROR, "timeout": ProviderStatus.DOWN, "server_error": ProviderStatus.DEGRADED}.get(kind.value, ProviderStatus.DOWN)
                self.providers.set_health(spec.name, healthy=False, latency_ms=0, status=status, message=str(exc))
                results.append({"name": spec.name, "status": status.value, "healthy": False, "message": str(exc)})
        return results

    def execute(self, message: str, *, capability: str | None = None, policy: str | None = None) -> dict[str, Any]:
        text = message.strip()
        if not text:
            return {"ok": False, "error": "message is required"}
        capability = capability or infer_capability(text)
        if capability == "research":
            return self.research(text)
        self.refresh_providers()
        for spec in self.providers._providers.values():
            if spec.name in self.adapters and not self.providers._health[spec.name].healthy:
                self.providers.set_health(spec.name, healthy=True, latency_ms=0, status=ProviderStatus.ACTIVE)
        executor = ProviderExecutor(self.router, self.adapters, self.providers)
        result = executor.execute(capability, {"input": text, "query": text, "prompt": text, "text": text}, policy=policy or self.settings.routing_policy)
        data = result.data
        if isinstance(data, dict) and isinstance(data.get("choices"), list) and data["choices"]:
            message_obj = data["choices"][0].get("message", {})
            if isinstance(message_obj, dict) and message_obj.get("content") is not None:
                data = message_obj["content"]
        return {"ok": True, "type": "execution", "capability": capability, "data": data, "provider": result.provider, "model": result.model, "latency_ms": result.latency_ms, "attempts": result.attempts, "errors": result.errors}

    def research(self, question: str) -> dict[str, Any]:
        self.refresh_providers()
        route = self.router.select("search", policy=self.settings.routing_policy, limit=3)
        adapters = [self.adapters[item.name] for item in ([route.primary] if route.primary else []) + route.fallbacks if item.name in self.adapters]
        if not adapters:
            return {"ok": False, "type": "research", "error": "no search provider configured", "capability_gap": "search"}
        def search(query: str):
            sources = []
            for adapter in adapters:
                try:
                    response = adapter.execute({"query": query})
                    data = response.data if hasattr(response, "data") else response
                    for item in data.get("results", []) if isinstance(data, dict) else []:
                        if isinstance(item, dict) and item.get("url"):
                            sources.append(ResearchSource(str(item["url"]), str(item.get("title", "")), str(item.get("content", item.get("snippet", ""))), float(item.get("score", 0.0) or 0.0)))
                except Exception:
                    continue
            return sources
        result = ResearchEngine(search=search).run(question)
        return {"ok": True, "type": "research", "question": result.question, "queries": result.queries, "sources": [{"url": s.url, "title": s.title, "excerpt": s.excerpt, "quality": s.quality} for s in result.sources], "findings": result.findings}

    def capability_status(self) -> dict[str, Any]:
        configured = {spec.capability for spec in self.providers._providers.values() if spec.name in self.adapters}
        assessment = CapabilityAdvisor(self.capabilities, configured).assess([item.name for item in self.capabilities.list()])
        return {"missing": list(assessment.missing), "unknown": list(assessment.unknown), "suggestions": {k: list(v) for k, v in assessment.suggestions.items()}}

    def status(self) -> dict[str, Any]:
        return {"ok": True, "service": "barberian", "version": __version__, "routing_policy": self.settings.routing_policy, "providers": self.providers.snapshot(), "adapters": sorted(self.adapters), "capability_gaps": self.capability_status()}

    def handle(self, message: str) -> dict[str, Any]:
        text = message.strip()
        if not text:
            return {"ok": False, "error": "message is required"}
        lowered = text.lower()
        match = re.fullmatch(r"add\s+(.+?)\s+(mcp|skill)", lowered)
        if match:
            name, kind = match.groups(); return registry.add(kind, name)
        match = re.fullmatch(r"(?:list|show)\s+(mcp|skills?)", lowered)
        if match:
            kind = "skill" if match.group(1).startswith("skill") else "mcp"; return registry.list_items(kind)
        match = re.fullmatch(r"disable\s+(.+?)\s+(mcp|skill)", lowered)
        if match:
            name, kind = match.groups(); return registry.disable(kind, name)
        if lowered in {"api", "apis", "list apis", "show apis", "api status"}:
            return {"ok": True, "type": "providers", "items": self.refresh_providers()}
        if lowered in {"check api", "check apis", "check providers", "health check"}:
            return {"ok": True, "type": "provider_health", "items": self.check_providers()}
        if lowered in {"capabilities", "list capabilities", "missing capabilities"}:
            return {"ok": True, "type": "capabilities", **self.capability_status()}
        if lowered in {"status", "health", "system status"}:
            return self.status()
        return self.execute(text)


_default_agent = Agent()


def handle_message(message: str) -> dict[str, Any]:
    return _default_agent.handle(message)
