"""Sandbox policy boundary. Execution backends are intentionally isolated from agent logic."""

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SandboxPolicy:
    timeout_seconds: int = 60
    memory_mb: int = 512
    cpu_seconds: int = 30
    network: bool = False
    writable: bool = True


class Sandbox:
    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy()

    def validate_command(self, command: list[str]) -> None:
        if not command or any(not isinstance(item, str) or not item for item in command):
            raise ValueError("command must be a non-empty list of strings")

    def manifest(self, command: list[str]) -> dict:
        self.validate_command(command)
        return {"command": list(command), "policy": self.policy.__dict__ if hasattr(self.policy, "__dict__") else {
            "timeout_seconds": self.policy.timeout_seconds,
            "memory_mb": self.policy.memory_mb,
            "cpu_seconds": self.policy.cpu_seconds,
            "network": self.policy.network,
            "writable": self.policy.writable,
        }}
