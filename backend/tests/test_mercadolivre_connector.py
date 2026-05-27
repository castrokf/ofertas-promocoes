import asyncio

import pytest

from app.connectors.base import StorePaused
from app.connectors.mercadolivre import MercadoLivreConnector


def test_mercado_livre_parse_item_with_discount():
    item = {
        "id": "MLB123",
        "title": "SSD NVMe 1TB",
        "price": 299.9,
        "original_price": 399.9,
        "permalink": "https://www.mercadolivre.com.br/ssd-nvme-1tb/p/MLB123",
        "thumbnail": "http://example.com/thumb.jpg",
        "available_quantity": 10,
        "shipping": {"free_shipping": True},
        "seller": {"nickname": "Loja Oficial", "power_seller_status": "platinum"},
    }

    snapshot = MercadoLivreConnector()._parse_item(item, "ssd")

    assert snapshot is not None
    assert snapshot.store_slug == "mercado-livre"
    assert snapshot.current_price == 299.9
    assert snapshot.old_price == 399.9
    assert snapshot.image_url == "https://example.com/thumb.jpg"
    assert snapshot.stock_status == "in_stock"


def test_mercado_livre_requires_access_token(monkeypatch):
    monkeypatch.setenv("MERCADO_LIVRE_ACCESS_TOKEN", "")
    from app.core.config import get_settings

    get_settings.cache_clear()
    connector = MercadoLivreConnector()

    with pytest.raises(StorePaused, match="MERCADO_LIVRE_ACCESS_TOKEN"):
        asyncio.run(connector.collect(limit=1))
    get_settings.cache_clear()
