"""Defensive pre-deployment security gate for the Barberian project."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Iterable


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class GateStatus(str, Enum):
    PASS = "SECURITY GATE: PASS"
    WARNINGS = "SECURITY GATE: PASS WITH WARNINGS"
    BLOCKED = "SECURITY GATE: BLOCKED"


@dataclass(frozen=True, slots=True)
class Finding:
    severity: Severity
    category: str
    title: str
    path: str
    line: int | None = None
    evidence: str = ""
    remediation: str = ""


@dataclass(frozen=True, slots=True)
class SecurityReport:
    gate: GateStatus
    findings: tuple[Finding, ...]

    def to_dict(self) -> dict:
        return {
            "gate": self.gate.value,
            "summary": {severity.value: sum(f.severity == severity for f in self.findings) for severity in Severity},
            "findings": [asdict(f) | {"severity": f.severity.value} for f in self.findings],
        }


TEXT_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".md", ".txt", ".sh", ".ps1", ".env"}
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
SKIP_PATHS = {"README.md", "barberian/security_gate.py"}
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*[\"']([^\"'\s]{12,})[\"']"),
    re.compile(r"(?i)\b(?:api[_-]?key|secret|password|token|access[_-]?token|client[_-]?secret)\b\s*[:=]\s*(sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
)
DANGEROUS_SHELL = re.compile(r"(?i)(shell\s*=\s*True|os\.(?:system|popen)\s*\(|subprocess\.(?:run|Popen|call|check_call|check_output)\s*\([^\n]*shell\s*=\s*True)")
WEAK_HTTP = re.compile(r"(?i)(http://|verify\s*=\s*False)")
DEBUG_EXPOSURE = re.compile(r"(?i)(traceback\.print_exc\(|app\.debug\s*=\s*True|DEBUG\s*=\s*True)")


class SecurityGate:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def _files(self) -> Iterable[Path]:
        if not self.root.exists():
            return ()
        return (
            p for p in self.root.rglob("*")
            if p.is_file()
            and not any(part in SKIP_DIRS for part in p.parts)
            and str(p.relative_to(self.root)).replace("\\", "/") not in SKIP_PATHS
            and "tests/" not in str(p.relative_to(self.root)).replace("\\", "/")
            and (p.suffix.lower() in TEXT_EXTENSIONS or p.name in {"Dockerfile", "requirements.txt", "package-lock.json"})
        )

    def audit(self) -> SecurityReport:
        findings: list[Finding] = []
        for path in self._files():
            rel = str(path.relative_to(self.root)).replace("\\", "/")
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lines = text.splitlines()
            if path.name == ".env":
                findings.append(Finding(Severity.CRITICAL, "secrets", "Environment file is present in project tree", rel, remediation="Keep .env out of source control and use platform secret storage."))
            for number, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped and not stripped.startswith(("#", "//")) and any(pattern.search(line) for pattern in SECRET_PATTERNS):
                    findings.append(Finding(Severity.CRITICAL, "secrets", "Possible hard-coded secret", rel, number, "secret-like value detected and redacted", "Rotate exposed credentials and move them to secret/environment storage."))
                if DANGEROUS_SHELL.search(line):
                    findings.append(Finding(Severity.HIGH, "command-execution", "Shell execution requires security review", rel, number, "dangerous shell execution pattern detected", "Use structured argument arrays, strict allowlists and a hardened sandbox; never pass untrusted text to a shell."))
                if DEBUG_EXPOSURE.search(line):
                    findings.append(Finding(Severity.MEDIUM, "information-disclosure", "Debug/traceback exposure pattern", rel, number, "debug exposure pattern detected", "Disable debug mode and return generic production errors with request IDs."))
                if WEAK_HTTP.search(line) and not stripped.startswith(("#", "//")):
                    findings.append(Finding(Severity.MEDIUM, "transport", "Potential insecure HTTP/TLS verification configuration", rel, number, "plaintext HTTP or disabled verification pattern", "Use HTTPS and certificate verification for production traffic."))
            if path.name.lower() in {"dockerfile", "docker-compose.yml", "docker-compose.yaml"} and re.search(r"(?i)privileged\s*:\s*true|/var/run/docker.sock", text):
                findings.append(Finding(Severity.CRITICAL, "container", "Privileged container or Docker socket exposure", rel, remediation="Remove privileged mode and unnecessary Docker socket/host access."))
            if path.name in {".github/workflows/test.yml", "ci.yml", "deploy.yml"} and re.search(r"(?i)pull_request[^\n]*\n[\s\S]{0,800}(?:secrets\.|GITHUB_TOKEN)", text):
                findings.append(Finding(Severity.HIGH, "ci-cd", "Potential secret exposure to pull-request workflow", rel, remediation="Keep production secrets out of untrusted pull-request execution and use least-privilege workflow permissions."))
        gate = GateStatus.BLOCKED if any(f.severity in {Severity.CRITICAL, Severity.HIGH} for f in findings) else GateStatus.WARNINGS if findings else GateStatus.PASS
        return SecurityReport(gate, tuple(findings))


def run_security_gate(root: str | Path = ".") -> dict:
    return SecurityGate(root).audit().to_dict()
