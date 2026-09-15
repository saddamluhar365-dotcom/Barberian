import json
import threading
import urllib.request

from app import run


def test_capabilities_endpoint():
    server = threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10002}, daemon=True)
    server.start()
    with urllib.request.urlopen("http://127.0.0.1:10002/api/capabilities") as response:
        payload = json.load(response)
    assert payload["ok"] is True
    assert "llm" in payload["items"]


def test_mcp_and_skill_endpoints():
    server = threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10003}, daemon=True)
    server.start()
    for path in ("mcp", "skills"):
        with urllib.request.urlopen(f"http://127.0.0.1:10003/api/{path}") as response:
            payload = json.load(response)
        assert payload["ok"] is True
