"""Thread-safe in-memory live execution event bus for the web layer."""

from dataclasses import dataclass, field
from threading import Condition, Lock
from time import time
from typing import Any


@dataclass(slots=True, frozen=True)
class ExecutionEvent:
    run_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time)


class EventBus:
    def __init__(self, max_events: int = 1000) -> None:
        self.max_events = max(1, int(max_events))
        self._events: list[ExecutionEvent] = []
        self._lock = Lock()
        self._condition = Condition(self._lock)

    def publish(self, event: ExecutionEvent) -> None:
        with self._condition:
            self._events.append(event)
            if len(self._events) > self.max_events:
                del self._events[:-self.max_events]
            self._condition.notify_all()

    def replay(self, run_id: str | None = None) -> list[ExecutionEvent]:
        with self._lock:
            if run_id is None:
                return list(self._events)
            return [event for event in self._events if event.run_id == run_id]

    def wait_for_events(self, run_id: str, timeout: float = 15.0) -> list[ExecutionEvent]:
        with self._condition:
            self._condition.wait_for(lambda: any(event.run_id == run_id for event in self._events), timeout=timeout)
            return [event for event in self._events if event.run_id == run_id]
