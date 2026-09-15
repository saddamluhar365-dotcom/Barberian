"""Deterministic agent loop that wraps planning, execution and verification."""

from dataclasses import dataclass, field
from typing import Callable, Any
from uuid import uuid4

from .planner import Planner, Plan
from .verifier import Verifier


@dataclass(slots=True)
class LoopStep:
    id: str
    action: str
    status: str = "PENDING"
    output: Any = None
    error: str | None = None


@dataclass(slots=True)
class LoopResult:
    run_id: str
    goal: str
    success: bool
    steps: list[LoopStep] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


class AgentLoop:
    def __init__(self, executor: Callable[[LoopStep], Any], planner: Planner | None = None, verifier: Verifier | None = None) -> None:
        self.executor = executor
        self.planner = planner or Planner()
        self.verifier = verifier or Verifier()

    def run(self, goal: str) -> LoopResult:
        plan: Plan = self.planner.create(goal)
        result = LoopResult(str(uuid4()), plan.goal, True)
        for planned in plan.steps:
            step = LoopStep(planned.id, planned.action)
            try:
                step.status = "RUNNING"
                step.output = self.executor(step)
                verification = self.verifier.verify(step.output)
                if not verification.passed:
                    step.status = "FAILED"
                    step.error = "; ".join(verification.issues)
                    result.success = False
                    result.issues.extend(verification.issues)
                    break
                step.status = "SUCCEEDED"
            except Exception as exc:
                step.status = "FAILED"
                step.error = str(exc)
                result.success = False
                result.issues.append(str(exc))
                break
            result.steps.append(step)
        return result
