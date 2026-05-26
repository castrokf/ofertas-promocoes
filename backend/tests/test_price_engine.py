from datetime import datetime, timedelta, timezone

from app.connectors.base import ProductSnapshot
from app.price_engine.decision import DecisionRules, evaluate_deal
from app.price_engine.history import PricePoint, calculate_price_stats


def test_calculate_price_stats_detects_new_low():
    now = datetime.now(timezone.utc)
    stats = calculate_price_stats(
        299,
        [
            PricePoint(price=399, checked_at=now - timedelta(days=2)),
            PricePoint(price=349, checked_at=now - timedelta(days=1)),
        ],
    )

    assert stats.avg_7d == 374
    assert stats.is_new_low_30d is True


def test_evaluate_deal_blocks_missing_image():
    snapshot = ProductSnapshot(
        store_slug="steam",
        external_id="1",
        title="Game",
        url="https://example.com",
        current_price=50,
        old_price=100,
        image_url=None,
        stock_status="in_stock",
    )
    stats = calculate_price_stats(50, [])

    decision = evaluate_deal(snapshot, stats, DecisionRules())

    assert decision.should_publish is False
    assert "missing image" in decision.reasons


def test_evaluate_deal_classifies_imperdivel():
    snapshot = ProductSnapshot(
        store_slug="steam",
        external_id="1",
        title="Game",
        url="https://example.com",
        current_price=40,
        old_price=100,
        image_url="https://example.com/img.jpg",
        stock_status="in_stock",
    )
    stats = calculate_price_stats(40, [])

    decision = evaluate_deal(snapshot, stats, DecisionRules())

    assert decision.should_publish is True
    assert decision.quality_label == "imperdivel"
