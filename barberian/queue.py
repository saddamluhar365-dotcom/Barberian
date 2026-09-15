"""Task queue abstraction with in-process and PostgreSQL-backed workers."""

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
        self._tasks: dict[str, QueueTask] = {}; self._pending: list[str] = []; self._lock = Lock()

    def enqueue(self, task: QueueTask) -> QueueTask:
        with self._lock:
            if task.id in self._tasks: raise ValueError(f"duplicate task: {task.id}")
            self._tasks[task.id] = task; self._pending.append(task.id); return task

    def claim(self) -> QueueTask | None:
        with self._lock:
            while self._pending:
                task = self._tasks[self._pending.pop(0)]
                if task.status != "PENDING": continue
                task.status = "RUNNING"; task.attempts += 1; return task
            return None

    def complete(self, task_id: str, result: Any) -> None:
        with self._lock:
            task = self._tasks[task_id]; task.status = "SUCCEEDED"; task.result = result; task.error = None

    def fail(self, task_id: str, error: str) -> None:
        with self._lock:
            task = self._tasks[task_id]; task.status = "FAILED"; task.error = error

    def get(self, task_id: str) -> QueueTask | None:
        with self._lock: return self._tasks.get(task_id)


class PostgresTaskQueue:
    """Uses PostgreSQL row locks so multiple worker processes can share the queue safely."""

    def __init__(self, database) -> None: self.database = database

    def claim(self, worker_id: str) -> QueueTask | None:
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("WITH picked AS (SELECT id FROM tasks WHERE state='PENDING' AND available_at<=now() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) UPDATE tasks SET state='RUNNING', attempts=attempts+1, locked_at=now(), locked_by=%s WHERE id IN (SELECT id FROM picked) RETURNING id,input,attempts", (worker_id,))
                row = cursor.fetchone()
                return QueueTask(str(row[0]), row[1] or {}, "RUNNING", int(row[2] or 0)) if row else None

    def complete(self, task_id: str, result: Any) -> None:
        try:
            from psycopg.types.json import Jsonb
            value = Jsonb(result)
        except ImportError:
            value = result
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE tasks SET state='SUCCEEDED', output=%s, locked_at=NULL, locked_by=NULL WHERE id=%s", (value, task_id))

    def fail(self, task_id: str, error: str) -> None:
        try:
            from psycopg.types.json import Jsonb
            value = Jsonb({"error": error})
        except ImportError:
            value = {"error": error}
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE tasks SET state='FAILED', output=%s, locked_at=NULL, locked_by=NULL WHERE id=%s", (value, task_id))
