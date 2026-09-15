"""Worker loop for queued tasks. The queue backend can be replaced by PostgreSQL/Cloud Tasks."""

import time
from typing import Callable

from .queue import InMemoryTaskQueue, QueueTask


class Worker:
    def __init__(self, queue: InMemoryTaskQueue, handler: Callable[[QueueTask], object], *, poll_seconds: float = 1.0) -> None:
        self.queue = queue
        self.handler = handler
        self.poll_seconds = max(0.05, poll_seconds)
        self.running = False

    def run_once(self) -> bool:
        task = self.queue.claim()
        if task is None:
            return False
        try:
            result = self.handler(task)
            self.queue.complete(task.id, result)
        except Exception as exc:
            self.queue.fail(task.id, str(exc))
        return True

    def run_forever(self) -> None:
        self.running = True
        while self.running:
            if not self.run_once():
                time.sleep(self.poll_seconds)

    def stop(self) -> None:
        self.running = False
