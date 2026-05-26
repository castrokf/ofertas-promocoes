from __future__ import annotations

from dataclasses import dataclass, field

from app.connectors.base import ProductSnapshot
from app.price_engine.history import PriceStats


@dataclass(slots=True)
class DecisionRules:
    min_discount_percent: float = 15
    max_shipping_ratio: float = 0.25
    excellent_discount_percent: float = 35
    incredible_discount_percent: float = 50
    price_error_drop_percent: float = 70


@dataclass(slots=True)
class DealDecision:
    should_publish: bool
    quality_label: str
    score: float
    reasons: list[str] = field(default_factory=list)
    requires_manual_approval: bool = False


def _discount(old_price: float | None, current_price: float) -> float:
    if not old_price or old_price <= current_price:
        return 0.0
    return round(((old_price - current_price) / old_price) * 100, 2)


def evaluate_deal(
    snapshot: ProductSnapshot,
    stats: PriceStats,
    rules: DecisionRules,
    target_price: float | None = None,
    store_trust_score: float = 1.0,
    duplicate_recently_posted: bool = False,
) -> DealDecision:
    reasons: list[str] = []
    discount_percent = _discount(snapshot.old_price, snapshot.current_price)
    below_avg_30d = stats.avg_30d is not None and snapshot.current_price < stats.avg_30d
    below_target = target_price is not None and snapshot.current_price <= target_price

    if duplicate_recently_posted:
        reasons.append("duplicate cooldown active")
    if snapshot.stock_status.lower() in {"out_of_stock", "sem estoque", "indisponivel", "sold_out"}:
        reasons.append("product out of stock")
    if not snapshot.image_url:
        reasons.append("missing image")
    if store_trust_score < 0.65:
        reasons.append("low store trust score")
    if snapshot.shipping_price and snapshot.shipping_price > snapshot.current_price * rules.max_shipping_ratio:
        reasons.append("shipping price too high")
    if discount_percent < rules.min_discount_percent and not below_target and not stats.is_new_low_30d:
        reasons.append("discount below minimum")
    if stats.avg_30d and snapshot.current_price >= stats.avg_30d and not below_target and not stats.is_new_low_30d:
        reasons.append("price is not below recent average")

    quality = "normal"
    if discount_percent >= rules.incredible_discount_percent or below_target:
        quality = "imperdivel"
    elif discount_percent >= rules.excellent_discount_percent or stats.is_new_low_30d:
        quality = "excelente"
    elif below_avg_30d:
        quality = "boa"

    requires_review = discount_percent >= rules.price_error_drop_percent
    if requires_review:
        quality = "possivel erro de preco"
        reasons.append("large price drop requires manual review")

    score = discount_percent * 3
    if below_avg_30d:
        score += 20
    if stats.is_new_low_30d:
        score += 25
    if below_target:
        score += 30
    score += max(store_trust_score, 0) * 10

    blocking_reasons = [reason for reason in reasons if reason != "large price drop requires manual review"]
    return DealDecision(
        should_publish=not blocking_reasons,
        quality_label=quality,
        score=round(score, 2),
        reasons=reasons,
        requires_manual_approval=requires_review,
    )
