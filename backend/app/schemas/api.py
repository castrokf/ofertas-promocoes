from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StoreCreate(BaseModel):
    name: str
    slug: str
    base_url: str
    collect_method: str = "public_page"
    supports_affiliate: bool = False
    rate_limit_per_minute: int = 20
    trust_score: float = 1.0


class StoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    base_url: str
    collect_method: str
    status: str
    supports_affiliate: bool
    rate_limit_per_minute: int
    trust_score: float


class CategoryCreate(BaseModel):
    name: str
    slug: str
    min_discount_percent: float = 15


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    is_active: bool
    min_discount_percent: float


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    brand: str | None = None
    url: str
    image_url: str | None = None
    target_price: float | None = None
    is_blocked: bool
    created_at: datetime


class AlertRuleCreate(BaseModel):
    name: str
    category_id: UUID | None = None
    product_id: UUID | None = None
    min_discount_percent: float = 15
    target_price: float | None = None
    max_shipping_price: float | None = None
    cooldown_hours: int = 12
    auto_publish: bool = False


class AlertRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    min_discount_percent: float
    target_price: float | None = None
    cooldown_hours: int
    is_active: bool
    auto_publish: bool


class PublishChannelCreate(BaseModel):
    name: str
    channel_type: str
    config: dict = Field(default_factory=dict)
    is_active: bool = True


class PublishChannelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    channel_type: str
    is_active: bool
    config: dict


class DealRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    quality_label: str
    score: float
    current_price: float
    old_price: float | None = None
    discount_percent: float
    affiliate_url: str | None = None
    requires_manual_approval: bool
    decision_reasons: list
    created_at: datetime


class DealCard(BaseModel):
    id: UUID
    title: str
    store: str
    category: str | None = None
    image_url: str | None = None
    current_price: float
    old_price: float | None = None
    discount_percent: float
    quality_label: str
    score: float
    affiliate_url: str | None = None
    message_twitter: str
    created_at: datetime


class RefreshRequest(BaseModel):
    segment: str = "games"
    store_slugs: list[str] | None = None
    limit: int = 50


class RefreshResponse(BaseModel):
    collected: int
    created_or_updated_products: int
    deals_created: int
    errors: list[str] = Field(default_factory=list)


class MetricsSummary(BaseModel):
    total_products: int
    total_deals: int
    total_publications: int
    published_deals: int
    avg_discount: float
    deals_by_store: list[dict]
    deals_by_category: list[dict]


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonitoredUrlCreate(BaseModel):
    store_id: UUID
    category_id: UUID | None = None
    url: HttpUrl
    collect_frequency_seconds: int = 300
    priority: int = 5


class MonitoredUrlRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    store_id: UUID
    category_id: UUID | None = None
    url: str
    collect_frequency_seconds: int
    priority: int
    is_active: bool
    last_checked_at: datetime | None = None


class LogEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    level: str
    source: str
    message: str
    context: dict
    created_at: datetime
