"""Apply the idempotent PostgreSQL schema using DATABASE_URL."""

from pathlib import Path
import os

from barberian.database import Database, DatabaseConfig


def migrate() -> None:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    sql = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with Database(DatabaseConfig(url)).connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)


if __name__ == "__main__":
    migrate()
