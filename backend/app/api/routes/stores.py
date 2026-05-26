from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession, require_admin
from app.models import Store, StoreCollectMethod, StoreStatus
from app.schemas import StoreCreate, StoreRead


router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("", response_model=list[StoreRead])
def list_stores(db: DbSession):
    return db.scalars(select(Store).order_by(Store.name)).all()


@router.post("", response_model=StoreRead)
def create_store(payload: StoreCreate, db: DbSession):
    if db.scalar(select(Store).where(Store.slug == payload.slug)):
        raise HTTPException(status_code=409, detail="Store already exists")
    store = Store(
        name=payload.name,
        slug=payload.slug,
        base_url=payload.base_url,
        collect_method=StoreCollectMethod(payload.collect_method),
        status=StoreStatus.active,
        supports_affiliate=payload.supports_affiliate,
        rate_limit_per_minute=payload.rate_limit_per_minute,
        trust_score=payload.trust_score,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.patch("/{store_id}/status", response_model=StoreRead)
def update_status(store_id: str, status: StoreStatus, db: DbSession):
    store = db.get(Store, store_id)
    if store is None:
        raise HTTPException(status_code=404, detail="Store not found")
    store.status = status
    db.commit()
    db.refresh(store)
    return store
