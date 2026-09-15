"""Minimal MCP JSON-RPC transport boundary for HTTP MCP servers."""

import json
from urllib import request
from urllib.error import HTTPError, URLError
from typing import Any


class MCPClient:
    def __init__(self, url: str, *, timeout: float = 30.0) -> None:
        if not url.strip():
            raise ValueError("MCP URL is required")
        self.url = url
        self.timeout = max(1.0, timeout)
        self._next_id = 0

    def request_payload(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not method.strip():
            raise ValueError("MCP method is required")
        self._next_id += 1
        return {"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params or {}}

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = self.request_payload(method, params)
        req = request.Request(self.url, data=json.dumps(payload).encode(), method="POST", headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                raw = response.read().decode()
        except HTTPError as exc:
            raise RuntimeError(f"MCP HTTP {exc.code}") from exc
        except URLError as exc:
            raise ConnectionError(f"MCP network error: {exc.reason}") from exc
        if raw.startswith("data:"):
            raw = next((line[5:].strip() for line in raw.splitlines() if line.startswith("data:")), "{}")
        result = json.loads(raw)
        if "error" in result:
            raise RuntimeError(str(result["error"]))
        return result.get("result", result)

    def list_tools(self) -> dict[str, Any]:
        return self.call("tools/list")

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.call("tools/call", {"name": name, "arguments": arguments or {}})
