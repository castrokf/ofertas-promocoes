from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AppSettings, DbSession, require_admin
from app.models import Deal, DealStatus, Product, PublishChannel
from app.schemas import DealCard, RefreshRequest, RefreshResponse
from app.services.deal_pipeline import DealPipeline
from app.services.message_service import MessageInput, MessageService
from app.services.publication_service import PublicationService


router = APIRouter(dependencies=[Depends(require_admin)])


def _to_card(deal: Deal) -> DealCard:
    product = deal.product
    store = product.store
    category = product.category.slug if product.category else None
    message = MessageService().twitter(
        MessageInput(
            title=product.title,
            store=store.name,
            current_price=deal.current_price,
            old_price=deal.old_price,
            discount_percent=deal.discount_percent,
            quality_label=deal.quality_label,
            link=deal.affiliate_url or product.url,
            category=category,
        )
    )
    return DealCard(
        id=deal.id,
        title=product.title,
        store=store.name,
        category=category,
        image_url=product.image_url,
        current_price=deal.current_price,
        old_price=deal.old_price,
        discount_percent=deal.discount_percent,
        quality_label=deal.quality_label,
        score=deal.score,
        affiliate_url=deal.affiliate_url,
        message_twitter=message,
        created_at=deal.created_at,
    )


@router.get("", response_model=list[DealCard])
def list_deals(db: DbSession, status: DealStatus | None = None, limit: int = 50):
    stmt = (
        select(Deal)
        .options(
            selectinload(Deal.product).selectinload(Product.store),
            selectinload(Deal.product).selectinload(Product.category),
        )
        .order_by(Deal.score.desc(), Deal.created_at.desc())
        .limit(min(limit, 200))
    )
    if status:
        stmt = stmt.where(Deal.status == status)
    return [_to_card(deal) for deal in db.scalars(stmt).all()]


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_deals(payload: RefreshRequest, db: DbSession, settings: AppSettings):
    result = await DealPipeline(db, settings).collect_and_evaluate(
        segment=payload.segment,
        store_slugs=payload.store_slugs,
        limit=payload.limit,
    )
    return RefreshResponse(**result.__dict__)


@router.post("/{deal_id}/approve")
def approve_deal(deal_id: str, db: DbSession):
    deal = db.get(Deal, deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    deal.status = DealStatus.approved
    db.commit()
    return {"ok": True}


@router.post("/{deal_id}/publish/{channel_id}")
async def publish_deal(deal_id: str, channel_id: str, db: DbSession, settings: AppSettings):
    deal = db.scalar(
        select(Deal)
        .options(
            selectinload(Deal.product).selectinload(Product.store),
            selectinload(Deal.product).selectinload(Product.category),
        )
        .where(Deal.id == deal_id)
    )
    channel = db.get(PublishChannel, channel_id)
    if deal is None or channel is None:
        raise HTTPException(status_code=404, detail="Deal or channel not found")
    publication = await PublicationService(db, settings).publish_deal(deal, channel)
    return {"status": publication.status, "error": publication.error_message}
