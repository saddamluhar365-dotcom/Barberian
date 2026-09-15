"""HTTP provider adapters using only the Python standard library."""

import json
from urllib import request

from .adapters import ProviderAdapter, ProviderResponse


class OpenAICompatibleAdapter(ProviderAdapter):
    def __init__(self, api_key: str, endpoint: str, model: str) -> None:
        if not api_key or not endpoint or not model:
            raise ValueError("api_key, endpoint and model are required")
        self.api_key = api_key
        self.endpoint = endpoint
        self.model = model
        self.name = "openai-compatible"

    def capabilities(self) -> list[str]:
        return ["llm"]

    def models(self) -> list[str]:
        return [self.model]

    def build_payload(self, request_data):
        text = request_data.get("input", "")
        return {"model": self.model, "messages": [{"role": "user", "content": text}]}

    def execute(self, request_data) -> ProviderResponse:
        payload = json.dumps(self.build_payload(request_data)).encode()
        req = request.Request(self.endpoint, data=payload, method="POST", headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        with request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode())
        return ProviderResponse(data=data, provider=self.name, model=self.model, raw=data)
