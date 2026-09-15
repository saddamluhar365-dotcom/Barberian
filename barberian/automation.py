"""Automation definitions and safe scheduling boundary."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True, frozen=True)
class Automation:
    id: str
    name: str
    prompt: str
    schedule: str
    enabled: bool = True
    metadata: dict = field(default_factory=dict)


class AutomationScheduler:
    def validate(self, automation: Automation) -> None:
        if not automation.id or not automation.name or not automation.prompt:
            raise ValueError("automation id, name and prompt are required")
        if not automation.schedule.strip():
            raise ValueError("schedule is required")

    def next_run(self, automation: Automation, now: datetime) -> datetime:
        self.validate(automation)
        raise NotImplementedError("connect a durable scheduler backend")
