from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.affiliate import AffiliateService
from app.connectors import CONNECTOR_REGISTRY, get_connector
from app.connectors.base import ProductSnapshot, StorePaused
from app.core.config import Settings
from app.models import (
    Category,
    Deal,
    DealStatus,
    PriceHistory,
    Product,
    Store,
    StoreCollectMethod,
    StoreStatus,
)
from app.price_engine import PricePoint, calculate_price_stats, evaluate_deal
from app.price_engine.decision import DecisionRules
from app.services.duplicate_guard import DuplicateGuard
from app.services.log_service import LogService


@dataclass(slots=True)
class PipelineResult:
    collected: int = 0
    created_or_updated_products: int = 0
    deals_created: int = 0
    errors: list[str] = field(default_factory=list)


def normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def slugify(value: str) -> str:
    value = normalize_title(value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


class DealPipeline:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.affiliate = AffiliateService(settings)
        self.logs = LogService(db)

    async def collect_and_evaluate(
        self,
        segment: str = "games",
        store_slugs: list[str] | None = None,
        limit: int = 50,
    ) -> PipelineResult:
        result = PipelineResult()
        slugs = store_slugs or self._default_store_slugs(segment)
        disabled_stores = {slugify(store) for store in self.settings.disabled_stores}

        for store_slug in slugs:
            if store_slug in disabled_stores:
                continue
            connector_cls = CONNECTOR_REGISTRY.get(store_slug)
            if connector_cls is None:
                result.errors.append(f"connector not registered: {store_slug}")
                self.logs.record("warning", "connector", "Connector not registered", {"store_slug": store_slug})
                continue
            connector = get_connector(store_slug)
            self._ensure_store(connector)
            try:
                snapshots = await connector.collect(limit=limit)
            except StorePaused as exc:
                result.errors.append(str(exc))
                self.logs.record("warning", store_slug, str(exc))
                continue
            except Exception as exc:
                result.errors.append(f"{store_slug}: {exc}")
                self.logs.record("error", store_slug, "Collection failed", {"error": str(exc)})
                continue

            result.collected += len(snapshots)
            self.logs.record("info", store_slug, "Snapshots collected", {"count": len(snapshots)})
            for snapshot in snapshots:
                try:
                    product, price_history = self._persist_snapshot(snapshot)
                    result.created_or_updated_products += 1
                    deal = self._evaluate_snapshot(product, price_history, snapshot)
                    if deal:
                        result.deals_created += 1
                except Exception as exc:
                    result.errors.append(f"{store_slug}: snapshot failed: {exc}")
                    self.logs.record(
                        "error",
                        store_slug,
                        "Snapshot processing failed",
                        {"external_id": snapshot.external_id, "error": str(exc)},
                    )

        self.db.commit()
        return result

    def _default_store_slugs(self, segment: str) -> list[str]:
        if segment == "games":
            return [
                "steam",
                "nuuvem",
                "epic-games",
                "green-man-gaming",
                "gog",
                "xbox-store",
                "playstation-store",
                "nintendo-eshop",
            ]
        if segment == "hardware":
            return [
                "amazon",
                "mercado-livre",
                "aliexpress",
                "magazine-luiza",
                "shopee",
                "kabum",
                "terabyte",
                "pichau",
            ]
        return list(CONNECTOR_REGISTRY.keys())

    def _ensure_store(self, connector) -> Store:
        store = self.db.scalar(select(Store).where(Store.slug == connector.store_slug))
        if store:
            return store
        store = Store(
            name=connector.store_name,
            slug=connector.store_slug,
            base_url=connector.base_url,
            collect_method=StoreCollectMethod(connector.collect_method),
            status=StoreStatus.active,
            rate_limit_per_minute=connector.rate_limit_per_minute,
            supports_affiliate=connector.store_slug in {"amazon", "mercado-livre", "aliexpress"},
            trust_score=1.0,
        )
        self.db.add(store)
        self.db.flush()
        return store

    def _ensure_category(self, category_slug: str | None) -> Category | None:
        if not category_slug:
            return None
        category = self.db.scalar(select(Category).where(Category.slug == category_slug))
        if category:
            return category
        category = Category(name=category_slug.replace("-", " ").title(), slug=category_slug)
        self.db.add(category)
        self.db.flush()
        return category

    def _persist_snapshot(self, snapshot: ProductSnapshot) -> tuple[Product, PriceHistory]:
        store = self.db.scalar(select(Store).where(Store.slug == snapshot.store_slug))
        if store is None:
            raise ValueError(f"store not found for snapshot: {snapshot.store_slug}")
        category = self._ensure_category(snapshot.category_slug)
        product = self.db.scalar(
            select(Product)
            .where(Product.store_id == store.id)
            .where(Product.external_id == snapshot.external_id)
        )
        if product is None:
            product = Product(
                store_id=store.id,
                category_id=category.id if category else None,
                external_id=snapshot.external_id,
                sku=snapshot.sku,
                title=snapshot.title,
                normalized_title=normalize_title(snapshot.title),
                brand=snapshot.brand,
                url=snapshot.url,
                image_url=snapshot.image_url,
                metadata_json={"seller_name": snapshot.seller_name, "seller_reputation": snapshot.seller_reputation},
            )
            self.db.add(product)
            self.db.flush()
        else:
            product.title = snapshot.title
            product.normalized_title = normalize_title(snapshot.title)
            product.url = snapshot.url
            product.image_url = snapshot.image_url or product.image_url
            product.category_id = category.id if category else product.category_id

        price_history = PriceHistory(
            product_id=product.id,
            price=snapshot.current_price,
            old_price=snapshot.old_price,
            pix_price=snapshot.pix_price,
            card_price=snapshot.card_price,
            boleto_price=snapshot.boleto_price,
            shipping_price=snapshot.shipping_price,
            stock_status=snapshot.stock_status,
            raw_payload=snapshot.raw_payload,
        )
        self.db.add(price_history)
        self.db.flush()
        return product, price_history

    def _evaluate_snapshot(
        self,
        product: Product,
        price_history: PriceHistory,
        snapshot: ProductSnapshot,
    ) -> Deal | None:
        history_rows = self.db.scalars(
            select(PriceHistory)
            .where(PriceHistory.product_id == product.id)
            .where(PriceHistory.id != price_history.id)
            .order_by(PriceHistory.checked_at.desc())
            .limit(500)
        ).all()
        points = []
        for row in history_rows:
            if not row.checked_at:
                continue
            checked_at = row.checked_at
            if checked_at.tzinfo is None:
                checked_at = checked_at.replace(tzinfo=timezone.utc)
            else:
                checked_at = checked_at.astimezone(timezone.utc)
            points.append(PricePoint(price=row.price, checked_at=checked_at))
        stats = calculate_price_stats(snapshot.current_price, points)
        store = self.db.get(Store, product.store_id)
        duplicate_recent = DuplicateGuard(self.db).recently_published_same_price(
            product.id,
            snapshot.current_price,
            self.settings.repost_cooldown_hours,
        )
        decision = evaluate_deal(
            snapshot=snapshot,
            stats=stats,
            rules=DecisionRules(
                min_discount_percent=self.settings.min_discount_percent,
                max_shipping_ratio=self.settings.max_shipping_ratio,
                excellent_discount_percent=self.settings.excellent_discount_percent,
                incredible_discount_percent=self.settings.incredible_discount_percent,
                price_error_drop_percent=self.settings.price_error_drop_percent,
            ),
            target_price=product.target_price,
            store_trust_score=store.trust_score if store else 1.0,
            duplicate_recently_posted=duplicate_recent,
        )
        if not decision.should_publish:
            if decision.reasons:
                self.logs.record(
                    "info",
                    "price_engine",
                    "Offer ignored",
                    {"product_id": str(product.id), "reasons": decision.reasons[:5]},
                )
            return None

        affiliate_url, _is_monetized = self.affiliate.build_url(store.slug if store else "", product.url)
        status = DealStatus.needs_review if decision.requires_manual_approval else DealStatus.approved
        if self.settings.publish_mode == "semi_automatic":
            status = DealStatus.pending
        deal = Deal(
            product_id=product.id,
            price_history_id=price_history.id,
            status=status,
            quality_label=decision.quality_label,
            score=decision.score,
            current_price=snapshot.current_price,
            old_price=snapshot.old_price,
            discount_percent=((snapshot.old_price - snapshot.current_price) / snapshot.old_price * 100)
            if snapshot.old_price and snapshot.old_price > snapshot.current_price
            else 0,
            historical_low=stats.historical_low,
            avg_7d=stats.avg_7d,
            avg_30d=stats.avg_30d,
            avg_90d=stats.avg_90d,
            decision_reasons=decision.reasons,
            affiliate_url=affiliate_url,
            requires_manual_approval=decision.requires_manual_approval,
        )
        self.db.add(deal)
        self.db.flush()
        self.logs.record(
            "info",
            "price_engine",
            "Deal approved by rules",
            {"deal_id": str(deal.id), "product_id": str(product.id), "quality_label": deal.quality_label},
        )
        return deal


def avg_discount(db: Session) -> float:
    value = db.scalar(select(func.avg(Deal.discount_percent)))
    return round(float(value or 0), 2)
