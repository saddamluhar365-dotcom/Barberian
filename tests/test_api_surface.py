import json
import threading
import urllib.request

from app import run
from conftest import wait_for_url


def test_capabilities_endpoint():
    threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10002}, daemon=True).start()
    with wait_for_url("http://127.0.0.1:10002/api/capabilities") as response:
        payload = json.load(response)
    assert payload["ok"] is True
    assert "llm" in payload["items"]


def test_mcp_and_skill_endpoints():
    threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10003}, daemon=True).start()
    for path in ("mcp", "skills"):
        with wait_for_url(f"http://127.0.0.1:10003/api/{path}") as response:
            payload = json.load(response)
        assert payload["ok"] is True
