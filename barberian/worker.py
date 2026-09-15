"""Render worker entry point for durable PostgreSQL-backed tasks."""

import os
import socket
import time

from .agent import handle_message
from .database import Database, DatabaseConfig
from .queue import PostgresTaskQueue


def run_worker(poll_seconds: float = 2.0) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for the production worker")
    queue = PostgresTaskQueue(Database(DatabaseConfig(database_url)))
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    while True:
        task = queue.claim(worker_id)
        if task is None:
            time.sleep(max(0.1, poll_seconds)); continue
        try:
            message = str(task.payload.get("message", ""))
            result = handle_message(message)
            queue.complete(task.id, result)
        except Exception as exc:
            queue.fail(task.id, str(exc))


if __name__ == "__main__":
    run_worker()
