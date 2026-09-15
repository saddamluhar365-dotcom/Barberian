"""Task planning primitives for the Understand -> Plan -> Execute loop."""

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class PlanStep:
    id: str
    action: str
    capability: str | None = None
    depends_on: tuple[str, ...] = ()


@dataclass(slots=True)
class Plan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)


class Planner:
    def create(self, goal: str) -> Plan:
        goal = goal.strip()
        if not goal:
            raise ValueError("goal is required")
        return Plan(goal=goal, steps=[PlanStep(id="respond", action="respond")])
