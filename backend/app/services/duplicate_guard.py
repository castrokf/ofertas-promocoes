from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Deal, DealStatus


class DuplicateGuard:
    def __init__(self, db: Session) -> None:
        self.db = db

    def recently_published_same_price(self, product_id: UUID, price: float, cooldown_hours: int) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
        stmt = (
            select(Deal)
            .where(Deal.product_id == product_id)
            .where(Deal.status == DealStatus.published)
            .where(Deal.current_price == price)
            .where(Deal.created_at >= cutoff)
            .limit(1)
        )
        return self.db.scalar(stmt) is not None
