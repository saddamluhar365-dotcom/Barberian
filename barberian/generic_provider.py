"""Explicitly configured generic JSON HTTP provider adapter."""

import json
from urllib import request
from urllib.error import HTTPError, URLError
from typing import Any

from .adapters import ProviderAdapter, ProviderResponse


class GenericJSONAdapter(ProviderAdapter):
    def __init__(self, api_key: str, endpoint: str, *, name: str, capability: str = "custom", timeout: float = 60.0) -> None:
        if not api_key or not endpoint or not name:
            raise ValueError("api_key, endpoint and name are required")
        self.api_key, self.endpoint, self.name, self.capability, self.timeout = api_key, endpoint, name, capability, max(1.0, timeout)

    def capabilities(self) -> list[str]:
        return [self.capability]

    def build_payload(self, request_data: dict[str, Any]) -> dict[str, Any]:
        return dict(request_data)

    def execute(self, request_data) -> ProviderResponse:
        req = request.Request(self.endpoint, data=json.dumps(self.build_payload(request_data)).encode(), method="POST", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
        except HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"provider network error: {exc.reason}") from exc
        return ProviderResponse(data=data, provider=self.name, raw=data)
