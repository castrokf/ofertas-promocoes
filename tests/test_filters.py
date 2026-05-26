from config import Settings
from database.models import PriceHistorySummary
from filters.deal_filter import calculate_discount, is_good_deal, normalize_product_data


def test_calculate_discount():
    assert calculate_discount(1000, 800) == 20.0


def test_normalize_product_data():
    product = normalize_product_data(
        {
            "title": " SSD Kingston NV2 1TB ",
            "price": "R$ 349,90",
            "old_price": "R$ 499,90",
            "url": "https://example.com/produto?ref=abc",
            "store": "Amazon Brasil",
            "stock_status": "in_stock",
        }
    )

    assert product is not None
    assert product.current_price == 349.9
    assert product.discount_percent > 0
    assert product.url == "https://example.com/produto?ref=abc"


def test_is_good_deal_accepts_real_discount():
    settings = Settings()
    history = PriceHistorySummary(previous_price=999.0, lowest_price=950.0, is_new_low=True, has_history=True)
    product = normalize_product_data(
        {
            "title": "Placa de Video RTX 4070 Super ASUS",
            "price": "R$ 899,00",
            "old_price": "R$ 1.299,00",
            "url": "https://example.com/gpu",
            "store": "KaBuM",
            "stock_status": "in_stock",
        }
    )

    approved, reasons = is_good_deal(product, settings, history, already_posted=False)
    assert approved is True
    assert reasons == []


def test_is_good_deal_allows_unposted_deal_seen_before():
    settings = Settings()
    history = PriceHistorySummary(
        previous_price=89.9,
        lowest_price=89.9,
        is_new_low=True,
        has_history=True,
    )
    product = normalize_product_data(
        {
            "title": "Eternal Threads",
            "price": "R$ 89,90",
            "old_price": "R$ 399,90",
            "url": "https://example.com/game",
            "store": "Epic Games Store",
            "stock_status": "digital",
            "segment": "games",
        }
    )

    approved, reasons = is_good_deal(product, settings, history, already_posted=False)

    assert approved is True
    assert "preco nao esta menor que o ultimo salvo" not in reasons
