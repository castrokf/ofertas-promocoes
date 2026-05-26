from __future__ import annotations

from database.db import DatabaseManager
from database.models import PriceHistorySummary


def check_price_history(
    db: DatabaseManager,
    product_hash: str,
    current_price: float,
) -> PriceHistorySummary:
    previous_price, lowest_price = db.get_price_summary(product_hash)
    has_history = previous_price is not None or lowest_price is not None
    reference_low = lowest_price if lowest_price is not None else current_price

    return PriceHistorySummary(
        previous_price=previous_price,
        lowest_price=lowest_price,
        is_new_low=current_price <= reference_low,
        has_history=has_history,
    )
