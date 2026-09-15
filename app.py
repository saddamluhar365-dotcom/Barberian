"""Barberian HTTP entry point and JSON API."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import time
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from barberian.agent import _default_agent, handle_message
from barberian.capabilities import CapabilityRegistry
from barberian.config import Settings
from barberian.database import Database, DatabaseConfig
from barberian.events import EventBus, ExecutionEvent
from barberian.mcp import MCPRegistry
from barberian.queue import InMemoryTaskQueue, PostgresTaskQueue, QueueTask
from barberian.registry import list_items
from barberian.skills import SkillRegistry

WEB = Path(__file__).parent / "web" / "index.html"
CAPABILITIES = CapabilityRegistry(); MCP = MCPRegistry(); SKILLS = SkillRegistry(); EVENTS = EventBus(); LOCAL_TASKS = InMemoryTaskQueue()
MAX_REQUEST_BYTES = 1_048_576


def task_queue():
    url = os.getenv("DATABASE_URL")
    return PostgresTaskQueue(Database(DatabaseConfig(url))) if url else LOCAL_TASKS


def _security_headers(handler: BaseHTTPRequestHandler) -> None:
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.send_header("X-Frame-Options", "DENY")
    handler.send_header("Referrer-Policy", "no-referrer")
    handler.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    handler.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'")
    if os.getenv("TRUST_PROXY_TLS", "0").lower() in {"1", "true", "yes"}:
        handler.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")


class Handler(BaseHTTPRequestHandler):
    server_version = "Barberian/0.5"

    def log_message(self, format, *args):
        return

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        _security_headers(self)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path); path = parsed.path
        if path == "/api/health": return self.send_json({"ok": True, "service": "barberian", "status": "healthy"})
        if path == "/api/status": return self.send_json(_default_agent.status())
        if path == "/api/providers":
            if parse_qs(parsed.query).get("check", ["0"])[0] in {"1", "true"}: return self.send_json({"ok": True, "items": _default_agent.check_providers(), "checked": True})
            return self.send_json({"ok": True, "items": _default_agent.refresh_providers(), "checked": False})
        if path == "/api/models":
            return self.send_json({"ok": True, "items": [{"provider": x["name"], "model": x["model"], "capability": x["capability"]} for x in _default_agent.refresh_providers() if x.get("model")]})
        if path == "/api/capabilities": return self.send_json({"ok": True, "items": [x.name for x in CAPABILITIES.list()], "status": _default_agent.capability_status()})
        if path == "/api/mcp": return self.send_json({"ok": True, "items": MCP.list_servers()})
        if path == "/api/skills": return self.send_json({"ok": True, "items": [x.name for x in SKILLS.list()]})
        if path == "/api/integrations": return self.send_json({"ok": True, "mcp": list_items("mcp"), "skills": list_items("skill")})
        if path == "/api/tasks":
            task_id = parse_qs(parsed.query).get("id", [None])[0]
            if task_id:
                task = task_queue().get(task_id); payload = None if task is None else {"id": task.id, "status": task.status, "attempts": task.attempts, "result": task.result, "error": task.error}; return self.send_json({"ok": task is not None, "task": payload}, 200 if task else 404)
            return self.send_json({"ok": True, "items": []})
        if path == "/api/events":
            run_id = parse_qs(parsed.query).get("run_id", [None])[0]; body = "".join(f"data: {json.dumps({'run_id': e.run_id, 'event_type': e.event_type, 'payload': e.payload, 'created_at': e.created_at})}\n\n" for e in EVENTS.replay(run_id)).encode(); self.send_response(200); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.send_header("Content-Length", str(len(body))); _security_headers(self); self.end_headers(); self.wfile.write(body); return
        if path in ("/", "/index.html"):
            body = WEB.read_bytes(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); _security_headers(self); self.end_headers(); self.wfile.write(body); return
        self.send_json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            size = int(self.headers.get("Content-Length", 0))
            if size < 0 or size > MAX_REQUEST_BYTES: return self.send_json({"ok": False, "error": "request too large"}, 413)
            data = json.loads(self.rfile.read(size) or b"{}")
            if path == "/api/tasks":
                message = data.get("message", "")
                if not isinstance(message, str) or not message.strip() or len(message) > 100_000: return self.send_json({"ok": False, "error": "invalid message"}, 400)
                task = QueueTask(str(uuid4()), {"message": message}); task_queue().enqueue(task); EVENTS.publish(ExecutionEvent(task.id, "queued", {"message_length": len(message)})); return self.send_json({"ok": True, "task_id": task.id, "status": task.status}, 202)
            if path != "/api/chat": return self.send_json({"ok": False, "error": "not found"}, 404)
            message = data.get("message", "")
            if not isinstance(message, str) or not message.strip() or len(message) > 100_000: return self.send_json({"ok": False, "error": "invalid message"}, 400)
            run_id = str(uuid4()); EVENTS.publish(ExecutionEvent(run_id, "started", {"stage": "understand"})); started = time(); result = handle_message(message); EVENTS.publish(ExecutionEvent(run_id, "completed", {"ok": bool(result.get("ok")), "latency_ms": round((time() - started) * 1000)})); result["run_id"] = run_id; return self.send_json(result, 200 if result.get("ok") else 400)
        except (ValueError, json.JSONDecodeError): return self.send_json({"ok": False, "error": "invalid request"}, 400)
        except Exception: return self.send_json({"ok": False, "error": "internal error"}, 500)



def run(host: str | None = None, port: int | None = None):
    settings = Settings.from_env(); ThreadingHTTPServer((host or settings.host, port or settings.port), Handler).serve_forever()


if __name__ == "__main__": run()
