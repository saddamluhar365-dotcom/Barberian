"""In-process provider telemetry; durable aggregation belongs in provider_usage SQL."""

from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class Usage:
    requests: int = 0
    tokens: int = 0
    successes: int = 0
    failures: int = 0
    latency_total_ms: int = 0


class UsageTracker:
    def __init__(self) -> None:
        self._items: dict[str, Usage] = {}
        self._lock = Lock()

    def record(self, provider: str, *, tokens: int = 0, latency_ms: int = 0, success: bool) -> None:
        with self._lock:
            item = self._items.setdefault(provider.strip().lower(), Usage())
            item.requests += 1
            item.tokens += max(0, int(tokens))
            item.latency_total_ms += max(0, int(latency_ms))
            if success:
                item.successes += 1
            else:
                item.failures += 1

    def snapshot(self, provider: str) -> dict[str, int | float]:
        with self._lock:
            item = self._items.get(provider.strip().lower(), Usage())
            average = item.latency_total_ms / item.requests if item.requests else 0.0
            return {"requests": item.requests, "tokens": item.tokens, "successes": item.successes, "failures": item.failures, "average_latency_ms": average}

    def all(self) -> dict[str, dict]:
        return {name: self.snapshot(name) for name in sorted(self._items)}
