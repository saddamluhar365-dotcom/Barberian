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
    """Uses PostgreSQL row locks so multiple web/worker processes can share the queue safely."""
    def __init__(self, database) -> None: self.database = database

    @staticmethod
    def _json(value):
        try:
            from psycopg.types.json import Jsonb
            return Jsonb(value)
        except ImportError:
            return value

    def enqueue(self, task: QueueTask) -> QueueTask:
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO tasks (id, kind, state, input, idempotency_key) VALUES (%s, 'agent', 'PENDING', %s, %s)", (task.id, self._json(task.payload), task.id))
        return task

    def get(self, task_id: str) -> QueueTask | None:
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT id,state,input,output,attempts FROM tasks WHERE id=%s", (task_id,))
                row = cursor.fetchone()
        if not row: return None
        output = row[3] or {}
        return QueueTask(str(row[0]), row[2] or {}, str(row[1]), int(row[4] or 0), output if str(row[1]) == "SUCCEEDED" else None, output.get("error") if isinstance(output, dict) else None)

    def claim(self, worker_id: str) -> QueueTask | None:
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("WITH picked AS (SELECT id FROM tasks WHERE state='PENDING' AND available_at<=now() ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1) UPDATE tasks SET state='RUNNING', attempts=attempts+1, locked_at=now(), locked_by=%s WHERE id IN (SELECT id FROM picked) RETURNING id,input,attempts", (worker_id,))
                row = cursor.fetchone()
                return QueueTask(str(row[0]), row[1] or {}, "RUNNING", int(row[2] or 0)) if row else None

    def complete(self, task_id: str, result: Any) -> None:
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE tasks SET state='SUCCEEDED', output=%s, locked_at=NULL, locked_by=NULL WHERE id=%s", (self._json(result), task_id))

    def fail(self, task_id: str, error: str) -> None:
        with self.database.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("UPDATE tasks SET state='FAILED', output=%s, locked_at=NULL, locked_by=NULL WHERE id=%s", (self._json({"error": error}), task_id))
