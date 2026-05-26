from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import Deal, DealStatus, Product, PublishChannel
from app.services.deal_pipeline import DealPipeline
from app.services.publication_service import PublicationService


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks.collect_priority_products")
def collect_priority_products():
    return _run(_collect(segment="all", limit=25))


@celery_app.task(name="app.workers.tasks.collect_common_categories")
def collect_common_categories():
    return _run(_collect(segment="hardware", limit=50))


@celery_app.task(name="app.workers.tasks.collect_games")
def collect_games():
    return _run(_collect(segment="games", limit=50))


@celery_app.task(name="app.workers.tasks.refresh_price_history")
def refresh_price_history():
    return _run(_collect(segment="all", limit=100))


@celery_app.task(name="app.workers.tasks.publish_approved_deals")
def publish_approved_deals():
    return _run(_publish_approved())


async def _collect(segment: str, limit: int):
    settings = get_settings()
    with SessionLocal() as db:
        result = await DealPipeline(db, settings).collect_and_evaluate(segment=segment, limit=limit)
        return result.__dict__


async def _publish_approved():
    settings = get_settings()
    with SessionLocal() as db:
        channels = db.scalars(select(PublishChannel).where(PublishChannel.is_active.is_(True))).all()
        deals = db.scalars(
            select(Deal)
            .options(
                selectinload(Deal.product).selectinload(Product.store),
                selectinload(Deal.product).selectinload(Product.category),
            )
            .where(Deal.status == DealStatus.approved)
            .order_by(Deal.score.desc())
            .limit(20)
        ).all()
        service = PublicationService(db, settings)
        published = 0
        for deal in deals:
            for channel in channels:
                publication = await service.publish_deal(deal, channel)
                if publication.status.value == "success":
                    published += 1
        return {"published": published}
