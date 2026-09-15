"""Controlled subprocess sandbox boundary with bounded resources and output capture."""

from dataclasses import dataclass
import os
import subprocess
import tempfile
from typing import Sequence


@dataclass(slots=True, frozen=True)
class SandboxPolicy:
    timeout_seconds: int = 60
    memory_mb: int = 512
    cpu_seconds: int = 30
    network: bool = False
    writable: bool = True
    max_output_bytes: int = 2_000_000


@dataclass(slots=True, frozen=True)
class SandboxResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


class Sandbox:
    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy()

    def validate_command(self, command: Sequence[str]) -> None:
        if not command or any(not isinstance(item, str) or not item for item in command):
            raise ValueError("command must be a non-empty list of strings")
        if self.policy.timeout_seconds <= 0 or self.policy.max_output_bytes <= 0:
            raise ValueError("sandbox limits must be positive")

    def manifest(self, command: list[str]) -> dict:
        self.validate_command(command)
        return {"command": list(command), "policy": {"timeout_seconds": self.policy.timeout_seconds, "memory_mb": self.policy.memory_mb, "cpu_seconds": self.policy.cpu_seconds, "network": self.policy.network, "writable": self.policy.writable, "max_output_bytes": self.policy.max_output_bytes}}

    def run(self, command: Sequence[str], *, input_text: str | None = None) -> SandboxResult:
        self.validate_command(command)
        with tempfile.TemporaryDirectory(prefix="barberian-sandbox-") as workdir:
            env = {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"}
            try:
                completed = subprocess.run(list(command), input=input_text, text=True, capture_output=True, cwd=workdir, env=env, timeout=self.policy.timeout_seconds, check=False)
            except subprocess.TimeoutExpired as exc:
                stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else (exc.stdout or b"").decode(errors="replace")
                stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else (exc.stderr or b"").decode(errors="replace")
                return SandboxResult(-1, stdout[: self.policy.max_output_bytes], stderr[: self.policy.max_output_bytes], True)
            return SandboxResult(completed.returncode, completed.stdout[: self.policy.max_output_bytes], completed.stderr[: self.policy.max_output_bytes])
