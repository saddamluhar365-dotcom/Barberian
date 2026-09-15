"""PostgreSQL persistence boundary. Secrets are never serialized into status output."""

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


@dataclass(slots=True, frozen=True)
class DatabaseConfig:
    url: str

    def safe_url(self) -> str:
        parsed = urlsplit(self.url)
        if not parsed.scheme:
            return "configured"
        host = parsed.hostname or ""
        netloc = host
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


class Database:
    def __init__(self, config: DatabaseConfig) -> None:
        if not config.url:
            raise ValueError("database URL is required")
        self.config = config

    def public_status(self) -> dict[str, Any]:
        return {"configured": True, "backend": "postgresql", "url": self.config.safe_url()}

    def health(self) -> dict[str, Any]:
        try:
            with self.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            return {**self.public_status(), "healthy": True}
        except Exception as exc:
            return {**self.public_status(), "healthy": False, "error": exc.__class__.__name__}

    def connection(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgreSQL runtime access") from exc
        return psycopg.connect(self.config.url)

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> list[tuple]:
        if not sql.strip():
            raise ValueError("sql is required")
        with self.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params or ()))
                try:
                    return list(cursor.fetchall())
                except Exception:
                    return []
