"""Task planning primitives for Understand -> Plan -> Task Graph."""

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class PlanStep:
    id: str
    action: str
    capability: str | None = None
    depends_on: tuple[str, ...] = ()
    parallelizable: bool = True


@dataclass(slots=True)
class Plan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)

    def validate(self) -> None:
        ids = {step.id for step in self.steps}
        if len(ids) != len(self.steps):
            raise ValueError("duplicate plan step id")
        for step in self.steps:
            missing = [dep for dep in step.depends_on if dep not in ids]
            if missing:
                raise ValueError(f"step {step.id} has missing dependencies: {missing}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("plan dependency cycle detected")
            if node in visited:
                return
            visiting.add(node)
            step = next(item for item in self.steps if item.id == node)
            for dep in step.depends_on:
                visit(dep)
            visiting.remove(node)
            visited.add(node)

        for step in self.steps:
            visit(step.id)


class Planner:
    def create(self, goal: str) -> Plan:
        goal = goal.strip()
        if not goal:
            raise ValueError("goal is required")
        plan = Plan(goal=goal, steps=[PlanStep(id="respond", action="respond", capability="llm")])
        plan.validate()
        return plan
