"""GitHub operation contracts with explicit permission boundaries."""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True, frozen=True)
class GitHubRequest:
    operation: str
    repository: str
    payload: dict[str, Any]
    require_approval: bool = False


class GitHubClient(Protocol):
    def execute(self, request: GitHubRequest) -> dict[str, Any]: ...


class GitHubWorkflow:
    READ_OPERATIONS = {"repos", "issues", "branches", "files", "commits", "pulls", "actions", "releases"}
    WRITE_OPERATIONS = {"create_file", "update_file", "create_branch", "create_pr", "push"}

    def classify(self, operation: str) -> str:
        op = operation.strip().lower()
        if op in self.READ_OPERATIONS:
            return "read"
        if op in self.WRITE_OPERATIONS:
            return "write"
        raise ValueError(f"unsupported github operation: {operation}")

    def plan(self, request: GitHubRequest) -> list[str]:
        kind = self.classify(request.operation)
        steps = ["understand", "inspect", "validate"]
        if kind == "write":
            steps.extend(["modify", "test", "review"])
            if request.require_approval:
                steps.append("approval")
            steps.append("commit_or_pr")
        return steps
