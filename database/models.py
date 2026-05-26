from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ProductDeal:
    title: str
    category: str
    store: str
    current_price: float
    old_price: float | None
    discount_percent: float
    url: str
    affiliate_url: str = ""
    image_url: str = ""
    stock_status: str = "unknown"
    segment: str = "hardware"
    product_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PriceHistorySummary:
    previous_price: float | None = None
    lowest_price: float | None = None
    is_new_low: bool = False
    has_history: bool = False


@dataclass(slots=True)
class PublishResult:
    published: bool
    tweet_id: str | None = None
    posted_url: str | None = None
    text: str | None = None
    error: str | None = None


@dataclass(slots=True)
class ExecutionStats:
    offers_collected: int = 0
    offers_approved: int = 0
    offers_posted: int = 0
    errors: list[str] = field(default_factory=list)
    next_run_at: datetime | None = None
    last_run_started_at: datetime | None = None
    last_run_finished_at: datetime | None = None
