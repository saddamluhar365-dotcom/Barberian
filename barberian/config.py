"""Runtime configuration. Secrets are read only from environment at execution time."""

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Barberian"
    host: str = "0.0.0.0"
    port: int = 10000
    database_url: str | None = None
    google_drive_folder: str = "AI AGENT"
    routing_policy: str = "balanced"
    max_workers: int = 4
    request_timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "Barberian"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "10000")),
            database_url=os.getenv("DATABASE_URL"),
            google_drive_folder=os.getenv("GOOGLE_DRIVE_FOLDER", "AI AGENT"),
            routing_policy=os.getenv("ROUTING_POLICY", "balanced"),
            max_workers=max(1, int(os.getenv("MAX_WORKERS", "4"))),
            request_timeout_seconds=max(1.0, float(os.getenv("REQUEST_TIMEOUT_SECONDS", "60"))),
        )

    def public(self) -> dict[str, object]:
        return {
            "app_name": self.app_name,
            "host": self.host,
            "port": self.port,
            "routing_policy": self.routing_policy,
            "max_workers": self.max_workers,
            "request_timeout_seconds": self.request_timeout_seconds,
            "database_configured": bool(self.database_url),
        }
