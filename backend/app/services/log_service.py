from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import LogEntry


class LogService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def record(self, level: str, source: str, message: str, context: dict | None = None) -> None:
        self.db.add(
            LogEntry(
                level=level.upper(),
                source=source,
                message=message,
                context=context or {},
            )
        )
