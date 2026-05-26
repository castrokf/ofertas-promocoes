from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class PricePoint:
    price: float
    checked_at: datetime


@dataclass(slots=True)
class PriceStats:
    current_price: float
    historical_low: float | None
    avg_7d: float | None
    avg_30d: float | None
    avg_90d: float | None
    recent_high: float | None
    variation_percent: float
    is_new_low_30d: bool


def _average(points: list[PricePoint], cutoff: datetime) -> float | None:
    values = [point.price for point in points if point.checked_at >= cutoff]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def calculate_price_stats(current_price: float, history: list[PricePoint]) -> PriceStats:
    now = datetime.now(timezone.utc)
    historical_low = min((point.price for point in history), default=None)
    recent_high = max((point.price for point in history if point.checked_at >= now - timedelta(days=30)), default=None)
    avg_7d = _average(history, now - timedelta(days=7))
    avg_30d = _average(history, now - timedelta(days=30))
    avg_90d = _average(history, now - timedelta(days=90))

    reference = avg_30d or recent_high or historical_low or current_price
    variation_percent = 0.0
    if reference:
        variation_percent = round(((current_price - reference) / reference) * 100, 2)

    low_30d = min((point.price for point in history if point.checked_at >= now - timedelta(days=30)), default=None)
    return PriceStats(
        current_price=current_price,
        historical_low=historical_low,
        avg_7d=avg_7d,
        avg_30d=avg_30d,
        avg_90d=avg_90d,
        recent_high=recent_high,
        variation_percent=variation_percent,
        is_new_low_30d=low_30d is not None and current_price < low_30d,
    )
