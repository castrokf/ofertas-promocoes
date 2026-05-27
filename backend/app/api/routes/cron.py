from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import AppSettings, DbSession
from app.models import Deal, DealStatus, Product, PublishChannel
from app.services.deal_pipeline import DealPipeline
from app.services.publication_service import PublicationService


router = APIRouter()


@router.api_route("/run", methods=["GET", "POST"])
async def run_cron(
    db: DbSession,
    settings: AppSettings,
    token: str | None = Query(default=None),
    x_cron_secret: str | None = Header(default=None),
    segment: str = "games",
    limit: int = 50,
    publish: bool = True,
    max_publish: int = 5,
):
    provided_secret = token or x_cron_secret
    if not settings.cron_secret or provided_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    collect_result = await DealPipeline(db, settings).collect_and_evaluate(
        segment=segment,
        limit=min(limit, 100),
    )
    published = 0
    publication_errors: list[str] = []

    if publish:
        channels = db.scalars(select(PublishChannel).where(PublishChannel.is_active.is_(True))).all()
        deals = db.scalars(
            select(Deal)
            .options(
                selectinload(Deal.product).selectinload(Product.store),
                selectinload(Deal.product).selectinload(Product.category),
            )
            .where(Deal.status == DealStatus.approved)
            .order_by(Deal.score.desc(), Deal.created_at.desc())
            .limit(min(max_publish, 20))
        ).all()
        service = PublicationService(db, settings)
        for deal in deals:
            for channel in channels:
                publication = await service.publish_deal(deal, channel)
                if publication.status.value in {"success", "skipped"}:
                    published += 1
                if publication.error_message and not settings.publish_dry_run:
                    publication_errors.append(publication.error_message)

    return {
        "ok": True,
        "segment": segment,
        "collected": collect_result.collected,
        "deals_created": collect_result.deals_created,
        "published_or_dry_run": published,
        "errors": collect_result.errors + publication_errors,
        "dry_run": settings.publish_dry_run,
    }
