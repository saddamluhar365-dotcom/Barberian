"""MCP registry contracts. Transport-specific implementations can be registered later."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class MCPServer:
    name: str
    command: str | None = None
    url: str | None = None
    enabled: bool = True
    permissions: set[str] = field(default_factory=set)


@dataclass(slots=True, frozen=True)
class MCPTool:
    server: str
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)


class MCPRegistry:
    def __init__(self) -> None:
        self.servers: dict[str, MCPServer] = {}
        self.tools: dict[str, MCPTool] = {}

    def register_server(self, server: MCPServer) -> None:
        self.servers[server.name.strip().lower()] = server

    def register_tool(self, tool: MCPTool) -> None:
        key = f"{tool.server.strip().lower()}:{tool.name.strip().lower()}"
        self.tools[key] = tool

    def list_servers(self) -> list[dict[str, Any]]:
        return [{"name": s.name, "enabled": s.enabled, "url": s.url, "command": s.command} for s in self.servers.values()]
