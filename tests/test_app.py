import json
import threading

from app import run
from conftest import wait_for_url


def test_health_endpoint():
    threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10001}, daemon=True).start()
    with wait_for_url("http://127.0.0.1:10001/api/health") as response:
        assert json.load(response)["ok"] is True
