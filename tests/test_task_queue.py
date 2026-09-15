from barberian.queue import InMemoryTaskQueue, QueueTask


def test_queue_claims_and_completes_task():
    queue = InMemoryTaskQueue()
    task = QueueTask("t1", {"action": "test"})
    queue.enqueue(task)
    claimed = queue.claim()
    assert claimed.id == "t1"
    queue.complete("t1", {"ok": True})
    assert queue.get("t1").status == "SUCCEEDED"
    assert queue.get("t1").result == {"ok": True}
