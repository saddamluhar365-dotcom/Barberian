"""Anthropic Messages API adapter."""

import json
from urllib import request
from urllib.error import HTTPError, URLError

from .adapters import ProviderAdapter, ProviderResponse


class AnthropicAdapter(ProviderAdapter):
    def __init__(self, api_key: str, model: str, endpoint: str = "https://api.anthropic.com/v1/messages", timeout: float = 60.0) -> None:
        if not api_key or not model:
            raise ValueError("api_key and model are required")
        self.api_key, self.model, self.endpoint, self.timeout = api_key, model, endpoint, max(1.0, timeout)
        self.name = "anthropic"

    def capabilities(self) -> list[str]:
        return ["llm", "vision"]

    def models(self) -> list[str]:
        return [self.model]

    def build_payload(self, request_data):
        return {"model": self.model, "max_tokens": int(request_data.get("max_tokens", 1024)), "messages": [{"role": "user", "content": str(request_data.get("input", ""))}]}

    def execute(self, request_data) -> ProviderResponse:
        req = request.Request(self.endpoint, data=json.dumps(self.build_payload(request_data)).encode(), method="POST", headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
        except HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"provider network error: {exc.reason}") from exc
        content = data.get("content") if isinstance(data, dict) else None
        if isinstance(content, list) and content and isinstance(content[0], dict) and content[0].get("text") is not None:
            data = content[0]["text"]
        return ProviderResponse(data=data, provider=self.name, model=self.model, raw=data)
