from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import DbSession, require_admin
from app.models import LogEntry
from app.schemas import LogEntryRead


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[LogEntryRead])
def list_logs(db: DbSession, level: str | None = None, source: str | None = None, limit: int = 100):
    stmt = select(LogEntry).order_by(LogEntry.created_at.desc()).limit(min(limit, 500))
    if level:
        stmt = stmt.where(LogEntry.level == level.upper())
    if source:
        stmt = stmt.where(LogEntry.source == source)
    return db.scalars(stmt).all()
