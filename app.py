"""Barberian HTTP entry point and JSON API."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import time
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from barberian.agent import _default_agent, handle_message
from barberian.capabilities import CapabilityRegistry
from barberian.config import Settings
from barberian.events import EventBus, ExecutionEvent
from barberian.mcp import MCPRegistry
from barberian.planner import Planner
from barberian.queue import InMemoryTaskQueue, QueueTask
from barberian.registry import list_items
from barberian.skills import SkillRegistry

WEB = Path(__file__).parent / "web" / "index.html"
CAPABILITIES = CapabilityRegistry()
MCP = MCPRegistry()
SKILLS = SkillRegistry()
EVENTS = EventBus()
TASKS = InMemoryTaskQueue()
PLANNER = Planner()


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
            if parse_qs(parsed.query).get("check", ["0"])[0] in {"1", "true"}:
                return self.send_json({"ok": True, "items": _default_agent.check_providers(), "checked": True})
            return self.send_json({"ok": True, "items": _default_agent.refresh_providers(), "checked": False})
        if path == "/api/models":
            items = [{"provider": item["name"], "model": item["model"], "capability": item["capability"]} for item in _default_agent.refresh_providers() if item.get("model")]
            return self.send_json({"ok": True, "items": items})
        if path == "/api/capabilities":
            return self.send_json({"ok": True, "items": [item.name for item in CAPABILITIES.list()], "status": _default_agent.capability_status()})
        if path == "/api/mcp":
            return self.send_json({"ok": True, "items": MCP.list_servers()})
        if path == "/api/skills":
            return self.send_json({"ok": True, "items": [skill.name for skill in SKILLS.list()]})
        if path == "/api/integrations":
            return self.send_json({"ok": True, "mcp": list_items("mcp"), "skills": list_items("skill")})
        if path == "/api/tasks":
            task_id = parse_qs(parsed.query).get("id", [None])[0]
            if task_id:
                task = TASKS.get(task_id)
                return self.send_json({"ok": bool(task), "task": task.__dict__ if task and hasattr(task, "__dict__") else ({"id": task.id, "status": task.status, "attempts": task.attempts, "result": task.result, "error": task.error} if task else None)}, 200 if task else 404)
            return self.send_json({"ok": True, "items": []})
        if path == "/api/events":
            run_id = parse_qs(parsed.query).get("run_id", [None])[0]
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
        try:
            size = int(self.headers.get("Content-Length", 0))
            if size < 0 or size > 1_048_576:
                return self.send_json({"ok": False, "error": "request too large"}, 413)
            data = json.loads(self.rfile.read(size) or b"{}")
            if path == "/api/tasks":
                message = data.get("message", "")
                if not isinstance(message, str) or not message.strip():
                    return self.send_json({"ok": False, "error": "message is required"}, 400)
                task = QueueTask(str(uuid4()), {"message": message})
                TASKS.enqueue(task)
                EVENTS.publish(ExecutionEvent(task.id, "queued", {"message": message}))
                return self.send_json({"ok": True, "task_id": task.id, "status": task.status}, 202)
            if path != "/api/chat":
                return self.send_json({"ok": False, "error": "not found"}, 404)
            message = data.get("message", "")
            if not isinstance(message, str) or not message.strip():
                return self.send_json({"ok": False, "error": "message is required"}, 400)
            run_id = str(uuid4())
            EVENTS.publish(ExecutionEvent(run_id, "started", {"stage": "understand"}))
            started = time()
            result = handle_message(message)
            EVENTS.publish(ExecutionEvent(run_id, "completed", {"ok": bool(result.get("ok")), "latency_ms": round((time() - started) * 1000)}))
            result["run_id"] = run_id
            return self.send_json(result, 200 if result.get("ok") else 400)
        except (ValueError, json.JSONDecodeError):
            return self.send_json({"ok": False, "error": "invalid request"}, 400)
        except Exception:
            return self.send_json({"ok": False, "error": "internal error"}, 500)


def run(host: str | None = None, port: int | None = None):
    settings = Settings.from_env()
    server = ThreadingHTTPServer((host or settings.host, port or settings.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run()
