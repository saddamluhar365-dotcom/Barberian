"""Dependency-aware execution engine for short and resumable task graphs."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Any


class TaskState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass(slots=True)
class Task:
    id: str
    action: Callable[[], Any]
    dependencies: tuple[str, ...] = ()
    state: TaskState = TaskState.PENDING


@dataclass(slots=True)
class ExecutionResult:
    status: TaskState
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


class ExecutionEngine:
    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max(1, int(max_workers))
        self.tasks: dict[str, Task] = {}

    def add_task(self, task: Task) -> None:
        if task.id in self.tasks:
            raise ValueError(f"duplicate task: {task.id}")
        self.tasks[task.id] = task

    def _validate(self) -> None:
        for task in self.tasks.values():
            missing = [dep for dep in task.dependencies if dep not in self.tasks]
            if missing:
                raise ValueError(f"task {task.id} has missing dependencies: {missing}")
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("task dependency cycle detected")
            if node in visited:
                return
            visiting.add(node)
            for dep in self.tasks[node].dependencies:
                visit(dep)
            visiting.remove(node)
            visited.add(node)

        for task_id in self.tasks:
            visit(task_id)

    def run(self) -> ExecutionResult:
        self._validate()
        outputs: dict[str, Any] = {}
        errors: dict[str, str] = {}
        remaining = set(self.tasks)

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            while remaining:
                ready = [
                    self.tasks[item]
                    for item in remaining
                    if all(self.tasks[dep].state == TaskState.SUCCEEDED for dep in self.tasks[item].dependencies)
                ]
                blocked = [
                    self.tasks[item]
                    for item in remaining
                    if any(self.tasks[dep].state in (TaskState.FAILED, TaskState.BLOCKED) for dep in self.tasks[item].dependencies)
                ]
                for task in blocked:
                    task.state = TaskState.BLOCKED
                    remaining.remove(task.id)

                if not ready:
                    if remaining:
                        raise RuntimeError("execution graph cannot make progress")
                    break

                futures = {}
                for task in ready:
                    task.state = TaskState.RUNNING
                    futures[pool.submit(task.action)] = task
                    remaining.remove(task.id)

                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        outputs[task.id] = future.result()
                        task.state = TaskState.SUCCEEDED
                    except Exception as exc:
                        task.state = TaskState.FAILED
                        errors[task.id] = str(exc)

        status = TaskState.FAILED if errors else TaskState.SUCCEEDED
        return ExecutionResult(status=status, outputs=outputs, errors=errors)
