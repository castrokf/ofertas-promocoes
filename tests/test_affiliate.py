from affiliate.generic_affiliate import generate_affiliate_link
from config import Settings
from database.models import ProductDeal


def test_mercadolivre_affiliate_uses_matt_word_and_optional_tool():
    product = ProductDeal(
        title="Controle Xbox Wireless",
        category="controles",
        store="Mercado Livre",
        current_price=299.9,
        old_price=399.9,
        discount_percent=25,
        url="https://produto.mercadolivre.com.br/MLB-123-controle",
        stock_status="in_stock",
        product_hash="hash",
    )
    settings = Settings(
        mercadolivre_affiliate_id="ofertatech",
        mercadolivre_tool_id="twitter",
    )

    affiliate_url = generate_affiliate_link(product, settings)

    assert "matt_word=ofertatech" in affiliate_url
    assert "matt_tool=twitter" in affiliate_url


def test_aliexpress_without_affiliate_id_keeps_original_url():
    product = ProductDeal(
        title="Controle 8BitDo",
        category="controles",
        store="AliExpress",
        current_price=199.9,
        old_price=249.9,
        discount_percent=20,
        url="https://pt.aliexpress.com/item/123.html",
        stock_status="in_stock",
        product_hash="hash",
    )

    affiliate_url = generate_affiliate_link(product, Settings(aliexpress_affiliate_id=""))

    assert affiliate_url == product.url
