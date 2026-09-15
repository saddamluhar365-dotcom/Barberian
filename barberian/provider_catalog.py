"""Approved provider catalog. Key names are signals; entries define safe execution boundaries."""

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
    "anthropic": ProviderCatalogEntry("anthropic", "llm", "ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "https://api.anthropic.com/v1/messages", "claude-3-5-haiku-latest", adapter="anthropic"),
    "gemini": ProviderCatalogEntry("gemini", "llm", "GEMINI_API_KEY", "GEMINI_BASE_URL", "GEMINI_MODEL", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-2.5-flash"),
    "perplexity": ProviderCatalogEntry("perplexity", "search", "PERPLEXITY_API_KEY", "PERPLEXITY_BASE_URL", "PERPLEXITY_MODEL", "https://api.perplexity.ai/chat/completions", "sonar"),
    "tavily": ProviderCatalogEntry("tavily", "search", "TAVILY_API_KEY", "TAVILY_BASE_URL", None, "https://api.tavily.com/search", None, adapter="tavily"),
    "serper": ProviderCatalogEntry("serper", "search", "SERPER_API_KEY", "SERPER_BASE_URL", None, "https://google.serper.dev/search", None, adapter="serper"),
    "replicate": ProviderCatalogEntry("replicate", "image", "REPLICATE_API_TOKEN", "REPLICATE_BASE_URL", "REPLICATE_MODEL", "https://api.replicate.com/v1/predictions", None, adapter="replicate"),
    "runway": ProviderCatalogEntry("runway", "video", "RUNWAY_API_KEY", "RUNWAY_BASE_URL", "RUNWAY_MODEL", "https://api.dev.runwayml.com/v1", None, adapter="runway"),
    "elevenlabs": ProviderCatalogEntry("elevenlabs", "audio", "ELEVENLABS_API_KEY", "ELEVENLABS_BASE_URL", "ELEVENLABS_MODEL", "https://api.elevenlabs.io/v1", None, adapter="elevenlabs"),
}


def get(name: str) -> ProviderCatalogEntry | None:
    return CATALOG.get(name.strip().lower())
