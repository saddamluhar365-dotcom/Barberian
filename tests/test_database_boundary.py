from barberian.database import Database, DatabaseConfig


def test_database_configuration_is_safe_and_does_not_expose_credentials():
    db = Database(DatabaseConfig("postgresql://user:secret@db.example/app"))
    assert db.public_status()["backend"] == "postgresql"
    assert "secret" not in str(db.public_status())
