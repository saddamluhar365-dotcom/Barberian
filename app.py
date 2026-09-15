"""Barberian HTTP entry point and JSON API."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import time
from urllib.parse import urlparse
from uuid import uuid4

from barberian.agent import _default_agent, handle_message
from barberian.capabilities import CapabilityRegistry
from barberian.config import Settings
from barberian.events import EventBus, ExecutionEvent
from barberian.mcp import MCPRegistry
from barberian.registry import list_items
from barberian.skills import SkillRegistry

WEB = Path(__file__).parent / "web" / "index.html"
CAPABILITIES = CapabilityRegistry()
MCP = MCPRegistry()
SKILLS = SkillRegistry()
EVENTS = EventBus()


class Handler(BaseHTTPRequestHandler):
    server_version = "Barberian/0.4"

    def log_message(self, format, *args):
        return

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            return self.send_json({"ok": True, "service": "barberian", "status": "healthy"})
        if path == "/api/status":
            return self.send_json(_default_agent.status())
        if path == "/api/providers":
            if parsed.query.lower() in {"check=1", "check=true", "probe=1"}:
                return self.send_json({"ok": True, "items": _default_agent.check_providers(), "checked": True})
            return self.send_json({"ok": True, "items": _default_agent.refresh_providers(), "checked": False})
        if path == "/api/capabilities":
            return self.send_json({"ok": True, "items": [item.name for item in CAPABILITIES.list()], "status": _default_agent.capability_status()})
        if path == "/api/mcp":
            return self.send_json({"ok": True, "items": MCP.list_servers()})
        if path == "/api/skills":
            return self.send_json({"ok": True, "items": [skill.name for skill in SKILLS.list()]})
        if path == "/api/integrations":
            return self.send_json({"ok": True, "mcp": list_items("mcp"), "skills": list_items("skill")})
        if path == "/api/events":
            run_id = parsed.query.split("run_id=", 1)[1] if "run_id=" in parsed.query else None
            events = EVENTS.replay(run_id)
            body = "".join(f"data: {json.dumps({'run_id': e.run_id, 'event_type': e.event_type, 'payload': e.payload, 'created_at': e.created_at})}\n\n" for e in events).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if path in ("/", "/index.html"):
            body = WEB.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/chat":
            return self.send_json({"ok": False, "error": "not found"}, 404)
        run_id = str(uuid4())
        try:
            size = int(self.headers.get("Content-Length", 0))
            if size < 0 or size > 1_048_576:
                return self.send_json({"ok": False, "error": "request too large"}, 413)
            data = json.loads(self.rfile.read(size) or b"{}")
            message = data.get("message", "")
            if not isinstance(message, str) or not message.strip():
                return self.send_json({"ok": False, "error": "message is required"}, 400)
            EVENTS.publish(ExecutionEvent(run_id, "started", {"stage": "understand"}))
            started = time()
            result = handle_message(message)
            EVENTS.publish(ExecutionEvent(run_id, "completed", {"ok": bool(result.get("ok")), "latency_ms": round((time() - started) * 1000)}))
            result["run_id"] = run_id
            self.send_json(result, 200 if result.get("ok") else 400)
        except (ValueError, json.JSONDecodeError):
            EVENTS.publish(ExecutionEvent(run_id, "failed", {"error": "invalid request"}))
            self.send_json({"ok": False, "error": "invalid request", "run_id": run_id}, 400)
        except Exception:
            EVENTS.publish(ExecutionEvent(run_id, "failed", {"error": "internal error"}))
            self.send_json({"ok": False, "error": "internal error", "run_id": run_id}, 500)


def run(host: str | None = None, port: int | None = None):
    settings = Settings.from_env()
    server = ThreadingHTTPServer((host or settings.host, port or settings.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run()
