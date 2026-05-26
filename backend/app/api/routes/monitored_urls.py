from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_admin
from app.models import Category, MonitoredUrl, Store
from app.schemas import MonitoredUrlCreate, MonitoredUrlRead


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[MonitoredUrlRead])
def list_monitored_urls(db: DbSession, active: bool | None = None, limit: int = 100):
    stmt = select(MonitoredUrl).order_by(MonitoredUrl.priority.desc(), MonitoredUrl.created_at.desc()).limit(
        min(limit, 500)
    )
    if active is not None:
        stmt = stmt.where(MonitoredUrl.is_active.is_(active))
    return db.scalars(stmt).all()


@router.post("", response_model=MonitoredUrlRead)
def create_monitored_url(payload: MonitoredUrlCreate, db: DbSession):
    store = db.get(Store, payload.store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    if payload.category_id and db.get(Category, payload.category_id) is None:
        raise HTTPException(status_code=404, detail="Category not found")

    monitored_url = MonitoredUrl(
        store_id=payload.store_id,
        category_id=payload.category_id,
        url=str(payload.url),
        collect_frequency_seconds=payload.collect_frequency_seconds,
        priority=payload.priority,
    )
    db.add(monitored_url)
    db.commit()
    db.refresh(monitored_url)
    return monitored_url


@router.patch("/{monitored_url_id}/status")
def update_status(monitored_url_id: str, is_active: bool, db: DbSession):
    monitored_url = db.get(MonitoredUrl, monitored_url_id)
    if monitored_url is None:
        raise HTTPException(status_code=404, detail="Monitored URL not found")
    monitored_url.is_active = is_active
    db.commit()
    return {"ok": True}
