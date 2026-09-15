import json
import threading
from urllib.request import urlopen

from app import run


def _start(port):
    threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": port}, daemon=True).start()


def test_static_assets_and_csp():
    _start(10002)
    for path, content_type in (
        ("/", "text/html"),
        ("/css/app.css", "text/css"),
        ("/js/app.js", "application/javascript"),
    ):
        with urlopen(f"http://127.0.0.1:10002{path}", timeout=3) as response:
            body = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers["Content-Type"].startswith(content_type)
            assert response.headers["Content-Security-Policy"] == "default-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"
            assert body


def test_static_path_cannot_escape_web_root():
    _start(10003)
    try:
        urlopen("http://127.0.0.1:10003/../app.py", timeout=3)
    except Exception as exc:
        response = getattr(exc, "headers", None)
        assert response is not None
        assert getattr(exc, "code", None) == 404
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload["ok"] is False
    else:
        raise AssertionError("path traversal unexpectedly succeeded")
