"""Permission, approval and secret-safety primitives."""

from dataclasses import dataclass
from enum import Enum
from secrets import token_urlsafe
from threading import Lock


class Permission(str, Enum):
    WEB_READ = "web.read"
    IMAGE_GENERATE = "image.generate"
    FILE_CREATE = "file.create"
    FILE_DELETE = "file.delete"
    GIT_PUSH = "git.push"
    MCP_INSTALL = "mcp.install"
    EXTERNAL_PAYMENT = "external.payment"


@dataclass(slots=True, frozen=True)
class PermissionPolicy:
    allowed: frozenset[Permission] = frozenset({Permission.WEB_READ, Permission.IMAGE_GENERATE, Permission.FILE_CREATE})

    def check(self, permission: Permission) -> bool:
        return permission in self.allowed


class ApprovalManager:
    """One-time in-memory approvals; persistent audit storage belongs in the database layer."""

    def __init__(self) -> None:
        self._tokens: dict[str, Permission] = {}
        self._lock = Lock()

    def issue(self, permission: Permission) -> str:
        token = token_urlsafe(24)
        with self._lock:
            self._tokens[token] = permission
        return token

    def consume(self, token: str, permission: Permission) -> bool:
        with self._lock:
            expected = self._tokens.get(token)
            if expected != permission:
                return False
            del self._tokens[token]
            return True


def redact_secret(value: str, *, visible: int = 0) -> str:
    if not value:
        return ""
    if visible <= 0:
        return "***"
    return value[:visible] + "***"
