"""Permission and secret-safety primitives."""

from dataclasses import dataclass
from enum import Enum


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
    allowed: frozenset[Permission] = frozenset({
        Permission.WEB_READ,
        Permission.IMAGE_GENERATE,
        Permission.FILE_CREATE,
    })

    def check(self, permission: Permission) -> bool:
        return permission in self.allowed


def redact_secret(value: str, *, visible: int = 0) -> str:
    if not value:
        return ""
    if visible <= 0:
        return "***"
    return value[:visible] + "***"
