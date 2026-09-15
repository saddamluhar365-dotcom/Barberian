"""Barberian HTTP entry point."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from barberian.agent import _default_agent, handle_message
from barberian.config import Settings

WEB = Path(__file__).parent / "web" / "index.html"


class Handler(BaseHTTPRequestHandler):
    server_version = "Barberian/0.2"

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
        path = urlparse(self.path).path
        if path == "/api/health":
            return self.send_json({"ok": True, "service": "barberian", "status": "healthy"})
        if path == "/api/status":
            return self.send_json(_default_agent.status())
        if path == "/api/providers":
            return self.send_json({"ok": True, "items": _default_agent.refresh_providers()})
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
        try:
            size = int(self.headers.get("Content-Length", 0))
            if size < 0 or size > 1_048_576:
                return self.send_json({"ok": False, "error": "request too large"}, 413)
            data = json.loads(self.rfile.read(size) or b"{}")
            message = data.get("message", "")
            if not isinstance(message, str) or not message.strip():
                return self.send_json({"ok": False, "error": "message is required"}, 400)
            self.send_json(handle_message(message))
        except (ValueError, json.JSONDecodeError):
            self.send_json({"ok": False, "error": "invalid request"}, 400)
        except Exception as exc:
            self.send_json({"ok": False, "error": "internal error", "detail": str(exc)}, 500)


def run(host: str | None = None, port: int | None = None):
    settings = Settings.from_env()
    server = ThreadingHTTPServer((host or settings.host, port or settings.port), Handler)
    server.serve_forever()


if __name__ == "__main__":
    run()
