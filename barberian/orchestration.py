"""Durable orchestration concepts: runs, checkpoints, retry and idempotency."""

from dataclasses import dataclass, field
from hashlib import sha256
import json


@dataclass(slots=True)
class Checkpoint:
    step_id: str
    state: str
    output: object = None


@dataclass(slots=True)
class RunState:
    run_id: str
    checkpoints: dict[str, Checkpoint] = field(default_factory=dict)
    attempts: dict[str, int] = field(default_factory=dict)

    def checkpoint(self, step_id: str, state: str, output: object = None) -> None:
        self.checkpoints[step_id] = Checkpoint(step_id, state, output)


def idempotency_key(operation: str, payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    return sha256(operation.encode() + b":" + encoded).hexdigest()
