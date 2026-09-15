"""Approved provider catalog. Key names are signals; catalog entries define safe adapters."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderCatalogEntry:
    name: str
    capability: str
    key_env: str
    endpoint_env: str | None = None
    model_env: str | None = None
    default_endpoint: str | None = None
    default_model: str | None = None
    adapter: str = "http"


CATALOG = {
    "openai": ProviderCatalogEntry("openai", "llm", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "https://api.openai.com/v1/chat/completions", "gpt-4o-mini"),
    "openrouter": ProviderCatalogEntry("openrouter", "llm", "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "OPENROUTER_MODEL", "https://openrouter.ai/api/v1/chat/completions", "openai/gpt-4o-mini"),
    "groq": ProviderCatalogEntry("groq", "llm", "GROQ_API_KEY", "GROQ_BASE_URL", "GROQ_MODEL", "https://api.groq.com/openai/v1/chat/completions", "llama-3.1-8b-instant"),
    "mistral": ProviderCatalogEntry("mistral", "llm", "MISTRAL_API_KEY", "MISTRAL_BASE_URL", "MISTRAL_MODEL", "https://api.mistral.ai/v1/chat/completions", "mistral-small-latest"),
    "anthropic": ProviderCatalogEntry("anthropic", "llm", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "https://api.anthropic.com/v1/messages", "claude-3-5-haiku-latest"),
}


def get(name: str) -> ProviderCatalogEntry | None:
    return CATALOG.get(name.strip().lower())
