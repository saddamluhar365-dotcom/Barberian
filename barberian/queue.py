"""Task queue abstraction with an in-process backend for development and tests."""

from dataclasses import dataclass, field
from threading import Lock
from time import time
from typing import Any


@dataclass(slots=True)
class QueueTask:
    id: str
    payload: dict[str, Any]
    status: str = "PENDING"
    attempts: int = 0
    result: Any = None
    error: str | None = None
    created_at: float = field(default_factory=time)


class InMemoryTaskQueue:
    def __init__(self) -> None:
        self._tasks: dict[str, QueueTask] = {}
        self._pending: list[str] = []
        self._lock = Lock()

    def enqueue(self, task: QueueTask) -> QueueTask:
        with self._lock:
            if task.id in self._tasks:
                raise ValueError(f"duplicate task: {task.id}")
            self._tasks[task.id] = task
            self._pending.append(task.id)
            return task

    def claim(self) -> QueueTask | None:
        with self._lock:
            while self._pending:
                task_id = self._pending.pop(0)
                task = self._tasks[task_id]
                if task.status != "PENDING":
                    continue
                task.status = "RUNNING"
                task.attempts += 1
                return task
            return None

    def complete(self, task_id: str, result: Any) -> None:
        with self._lock:
            task = self._tasks[task_id]
            task.status = "SUCCEEDED"
            task.result = result
            task.error = None

    def fail(self, task_id: str, error: str) -> None:
        with self._lock:
            task = self._tasks[task_id]
            task.status = "FAILED"
            task.error = error

    def get(self, task_id: str) -> QueueTask | None:
        with self._lock:
            return self._tasks.get(task_id)
