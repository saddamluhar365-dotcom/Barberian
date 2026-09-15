"""HTTP provider adapters using the Python standard library."""

import json
from urllib import request
from urllib.error import HTTPError, URLError

from .adapters import ProviderAdapter, ProviderResponse
from .providers import ProviderErrorClass


class OpenAICompatibleAdapter(ProviderAdapter):
    """Adapter for providers exposing the OpenAI chat-completions contract."""

    def __init__(self, api_key: str, endpoint: str, model: str, *, name: str = "openai-compatible", timeout: float = 60.0) -> None:
        if not api_key or not endpoint or not model:
            raise ValueError("api_key, endpoint and model are required")
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.name = name
        self.timeout = max(1.0, float(timeout))

    def capabilities(self) -> list[str]:
        return ["llm"]

    def models(self) -> list[str]:
        return [self.model]

    def build_payload(self, request_data):
        text = request_data.get("input", "")
        payload = {"model": self.model, "messages": [{"role": "user", "content": text}]}
        if request_data.get("max_tokens") is not None:
            payload["max_tokens"] = int(request_data["max_tokens"])
        if request_data.get("temperature") is not None:
            payload["temperature"] = float(request_data["temperature"])
        return payload

    def execute(self, request_data) -> ProviderResponse:
        payload = json.dumps(self.build_payload(request_data)).encode()
        req = request.Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
        except HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"provider network error: {exc.reason}") from exc
        return ProviderResponse(data=data, provider=self.name, model=self.model, raw=data)

    def classify_error(self, error: BaseException) -> ProviderErrorClass:
        return super().classify_error(error)
