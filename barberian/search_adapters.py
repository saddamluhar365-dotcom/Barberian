"""Search provider adapters with normalized source results."""

import json
from urllib import request
from urllib.error import HTTPError, URLError

from .adapters import ProviderAdapter, ProviderResponse


class _SearchAdapter(ProviderAdapter):
    capability = "search"

    def __init__(self, api_key: str, endpoint: str, *, name: str, timeout: float = 30.0) -> None:
        if not api_key or not endpoint:
            raise ValueError("api_key and endpoint are required")
        self.api_key = api_key
        self.endpoint = endpoint
        self.name = name
        self.timeout = max(1.0, timeout)

    def capabilities(self) -> list[str]:
        return ["search"]

    def models(self) -> list[str]:
        return []

    def _post(self, payload: dict, headers: dict[str, str]) -> dict:
        body = json.dumps(payload).encode()
        req = request.Request(self.endpoint, data=body, method="POST", headers={"Content-Type": "application/json", **headers})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"provider network error: {exc.reason}") from exc


class TavilyAdapter(_SearchAdapter):
    def __init__(self, api_key: str, endpoint: str = "https://api.tavily.com/search") -> None:
        super().__init__(api_key, endpoint, name="tavily")

    def build_payload(self, request_data):
        return {"query": str(request_data.get("query", "")), "search_depth": request_data.get("search_depth", "advanced"), "max_results": int(request_data.get("max_results", 5))}

    def execute(self, request_data) -> ProviderResponse:
        data = self._post(self.build_payload(request_data), {"Authorization": f"Bearer {self.api_key}"})
        return ProviderResponse(data=data, provider=self.name, raw=data)


class SerperAdapter(_SearchAdapter):
    def __init__(self, api_key: str, endpoint: str = "https://google.serper.dev/search") -> None:
        super().__init__(api_key, endpoint, name="serper")

    def build_payload(self, request_data):
        return {"q": str(request_data.get("query", ""))}

    def execute(self, request_data) -> ProviderResponse:
        data = self._post(self.build_payload(request_data), {"X-API-KEY": self.api_key})
        return ProviderResponse(data=data, provider=self.name, raw=data)
