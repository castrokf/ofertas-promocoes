from database.models import PriceHistorySummary, ProductDeal
from publisher.post_generator import generate_tweet_text


def test_generate_tweet_text_includes_affiliate_disclosure():
    product = ProductDeal(
        title="Mouse Logitech G Pro X Superlight 2",
        category="mouses",
        store="Amazon Brasil",
        current_price=599.9,
        old_price=799.9,
        discount_percent=25.0,
        url="https://example.com/produto",
        affiliate_url="https://example.com/produto?tag=abc",
        stock_status="in_stock",
        segment="hardware",
        product_hash="hash",
    )

    text = generate_tweet_text(product, PriceHistorySummary(previous_price=799.9))
    assert "link afiliado" in text.lower()


def test_generate_tweet_text_for_free_game():
    product = ProductDeal(
        title="Indie Game Deluxe",
        category="jogos gratis temporarios",
        store="Epic Games Store",
        current_price=0.0,
        old_price=49.9,
        discount_percent=100.0,
        url="https://example.com/game",
        stock_status="digital",
        segment="games",
        product_hash="hash",
    )

    text = generate_tweet_text(product)
    assert "gratis" in text.lower()
