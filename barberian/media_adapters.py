"""HTTP media-generation adapters with normalized asynchronous job responses."""

import json
from urllib import request
from urllib.error import HTTPError, URLError

from .adapters import ProviderAdapter, ProviderResponse


class _JSONAdapter(ProviderAdapter):
    def __init__(self, api_key: str, endpoint: str, *, name: str, timeout: float = 60.0) -> None:
        if not api_key or not endpoint:
            raise ValueError("api_key and endpoint are required")
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.name = name
        self.timeout = max(1.0, timeout)

    def _post(self, payload: dict, headers: dict[str, str] | None = None) -> dict:
        req = request.Request(self.endpoint, data=json.dumps(payload).encode(), method="POST", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", **(headers or {})})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"provider network error: {exc.reason}") from exc


class ReplicateAdapter(_JSONAdapter):
    def __init__(self, api_key: str, model: str, endpoint: str = "https://api.replicate.com/v1/predictions") -> None:
        super().__init__(api_key, endpoint, name="replicate")
        self.model = model

    def capabilities(self) -> list[str]:
        return ["image", "video", "audio"]

    def build_payload(self, request_data):
        payload = {"version": self.model, "input": {}}
        for key in ("prompt", "image", "video", "audio", "width", "height", "duration"):
            if key in request_data:
                payload["input"][key] = request_data[key]
        return payload

    def execute(self, request_data) -> ProviderResponse:
        data = self._post(self.build_payload(request_data))
        return ProviderResponse(data=data, provider=self.name, model=self.model, raw=data)


class RunwayAdapter(_JSONAdapter):
    def __init__(self, api_key: str, model: str, endpoint: str = "https://api.dev.runwayml.com/v1/image_to_video") -> None:
        super().__init__(api_key, endpoint, name="runway")
        self.model = model

    def capabilities(self) -> list[str]:
        return ["video", "image"]

    def build_payload(self, request_data):
        payload = {"model": self.model, "promptText": str(request_data.get("prompt", ""))}
        if request_data.get("image_url"):
            payload["promptImage"] = request_data["image_url"]
        if request_data.get("duration") is not None:
            payload["duration"] = int(request_data["duration"])
        return payload

    def execute(self, request_data) -> ProviderResponse:
        data = self._post(self.build_payload(request_data), {"X-Runway-Version": "2024-11-06"})
        return ProviderResponse(data=data, provider=self.name, model=self.model, raw=data)


class ElevenLabsAdapter(_JSONAdapter):
    def __init__(self, api_key: str, voice_id: str, endpoint: str = "https://api.elevenlabs.io/v1/text-to-speech") -> None:
        self.voice_id = voice_id
        super().__init__(api_key, f"{endpoint.rstrip('/')}/{voice_id}", name="elevenlabs")

    def capabilities(self) -> list[str]:
        return ["audio"]

    def build_payload(self, request_data):
        return {"text": str(request_data.get("text", "")), "model_id": request_data.get("model_id", "eleven_multilingual_v2")}

    def execute(self, request_data) -> ProviderResponse:
        req = request.Request(self.endpoint, data=json.dumps(self.build_payload(request_data)).encode(), method="POST", headers={"xi-api-key": self.api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                data = response.read()
        except HTTPError as exc:
            raise RuntimeError(f"provider HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"provider network error: {exc.reason}") from exc
        return ProviderResponse(data=data, provider=self.name, metadata={"mime_type": "audio/mpeg", "bytes": len(data)})
