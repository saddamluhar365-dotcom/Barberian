import json
import threading
import urllib.request

from app import run


def test_health_endpoint():
    server = threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10001}, daemon=True)
    server.start()
    with urllib.request.urlopen("http://127.0.0.1:10001/api/health") as response:
        assert json.load(response)["ok"] is True
