import json
import threading
import urllib.request

from app import run


def test_task_submission_endpoint():
    server = threading.Thread(target=run, kwargs={"host": "127.0.0.1", "port": 10004}, daemon=True)
    server.start()
    request = urllib.request.Request("http://127.0.0.1:10004/api/tasks", data=json.dumps({"message": "hello"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    assert payload["ok"] is True
    assert payload["task_id"]
