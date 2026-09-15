"""Automation definitions and lightweight scheduling primitives."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re


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
        schedule = automation.schedule.strip().lower()
        if schedule in {"hourly", "every hour"}:
            return now + timedelta(hours=1)
        if schedule in {"daily", "every day"}:
            return now + timedelta(days=1)
        match = re.fullmatch(r"every\s+(\d+)\s*(m|min|minutes|h|hr|hours|d|day|days)", schedule)
        if match:
            amount, unit = int(match.group(1)), match.group(2)
            if unit.startswith("m"): return now + timedelta(minutes=amount)
            if unit.startswith("h"): return now + timedelta(hours=amount)
            return now + timedelta(days=amount)
        raise ValueError("unsupported schedule; use hourly, daily, or 'every Nh/Nm/Nd'")
