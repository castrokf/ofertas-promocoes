from database.models import PriceHistorySummary, ProductDeal
from publisher.manual_exporter import export_ready_posts


def test_export_ready_posts_writes_file(tmp_path):
    product = ProductDeal(
        title="Ghostrunner 2",
        category="jogos em promocao",
        store="Epic Games Store",
        current_price=32.39,
        old_price=161.99,
        discount_percent=80,
        url="https://store.epicgames.com/pt-BR/p/ghostrunner-2",
        stock_status="digital",
        segment="games",
        product_hash="hash",
    )

    output_path = export_ready_posts(
        approved_deals=[(product, PriceHistorySummary(), 240.0)],
        output_dir=tmp_path,
        max_posts=1,
    )

    content = output_path.read_text(encoding="utf-8")
    assert output_path.exists()
    assert "POST 1" in content
    assert "Ghostrunner 2" in content
    assert "https://store.epicgames.com/pt-BR/p/ghostrunner-2" in content
