"""Structured execution telemetry with secret-safe event payloads."""

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass(slots=True, frozen=True)
class ExecutionEvent:
    event_type: str
    run_id: str
    step_id: str | None = None
    provider: str | None = None
    model: str | None = None
    status: str | None = None
    latency_ms: int | None = None
    retry: int = 0
    fallback: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time)


class EventSink:
    def emit(self, event: ExecutionEvent) -> None:
        raise NotImplementedError


class MemoryEventSink(EventSink):
    def __init__(self) -> None:
        self.events: list[ExecutionEvent] = []

    def emit(self, event: ExecutionEvent) -> None:
        self.events.append(event)
