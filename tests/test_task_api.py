import json
import threading
import urllib.request

from app import run
from conftest import wait_for_url


def test_task_submission_endpoint():
    threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10004}, daemon=True).start()
    wait_for_url("http://127.0.0.1:10004/api/health").close()
    req = urllib.request.Request("http://127.0.0.1:10004/api/tasks", data=json.dumps({"message": "hello"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as response:
        payload = json.load(response)
    assert payload["ok"] is True
    assert payload["task_id"]
