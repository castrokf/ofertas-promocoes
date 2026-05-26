from pathlib import Path

from config import Settings
from main import configure_runtime_settings


def test_test_mode_uses_separate_database():
    settings = Settings(
        test_mode=True,
        db_path=Path("prod.sqlite3"),
        test_db_path=Path("test.sqlite3"),
    )

    configure_runtime_settings(settings)

    assert settings.db_path == Path("test.sqlite3")


def test_publish_mode_keeps_production_database():
    settings = Settings(
        test_mode=False,
        db_path=Path("prod.sqlite3"),
        test_db_path=Path("test.sqlite3"),
    )

    configure_runtime_settings(settings)

    assert settings.db_path == Path("prod.sqlite3")
