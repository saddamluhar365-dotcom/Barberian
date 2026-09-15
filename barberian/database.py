"""Database boundary. Production persistence uses PostgreSQL via DATABASE_URL."""

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class DatabaseConfig:
    url: str


class Database:
    def __init__(self, config: DatabaseConfig) -> None:
        if not config.url:
            raise ValueError("database URL is required")
        self.config = config

    def health(self) -> dict[str, Any]:
        return {"configured": True, "backend": "postgresql"}
