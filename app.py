import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from barberian.agent import handle_message

WEB = Path(__file__).parent / "web" / "index.html"


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/health":
            return self.send_json({"ok": True, "service": "barberian"})
        if self.path in ("/", "/index.html"):
            body = WEB.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_json({"ok": False, "error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/api/chat":
            return self.send_json({"ok": False, "error": "not found"}, 404)
        try:
            size = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(size) or b"{}")
            message = data.get("message", "")
            if not isinstance(message, str) or not message.strip():
                return self.send_json({"ok": False, "error": "message is required"}, 400)
            self.send_json(handle_message(message))
        except (ValueError, json.JSONDecodeError):
            self.send_json({"ok": False, "error": "invalid request"}, 400)


def run(host="0.0.0.0", port=10000):
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    run()
