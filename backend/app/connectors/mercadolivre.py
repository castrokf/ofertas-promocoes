from __future__ import annotations

import httpx

from app.connectors.base import BaseConnector, ProductSnapshot, StorePaused
from app.core.config import get_settings


HARDWARE_QUERIES: tuple[tuple[str, str], ...] = (
    ("placa de video rtx", "placas-de-video"),
    ("placa de video rx", "placas-de-video"),
    ("processador ryzen", "processadores"),
    ("processador intel", "processadores"),
    ("memoria ram ddr4 16gb", "memoria-ram"),
    ("memoria ram ddr5", "memoria-ram"),
    ("ssd nvme 1tb", "ssd"),
    ("ssd sata 1tb", "ssd"),
    ("monitor gamer 144hz", "monitores"),
    ("teclado mecanico gamer", "teclados"),
    ("mouse gamer", "mouses"),
    ("headset gamer", "headsets"),
    ("cadeira gamer", "cadeiras-gamer"),
    ("notebook gamer", "notebooks"),
    ("controle xbox", "controles"),
    ("console playstation 5", "consoles"),
)


class MercadoLivreConnector(BaseConnector):
    store_slug = "mercado-livre"
    store_name = "Mercado Livre"
    base_url = "https://api.mercadolibre.com"
    collect_method = "api"
    rate_limit_per_minute = 20

    async def collect(self, keywords: list[str] | None = None, limit: int = 50) -> list[ProductSnapshot]:
        settings = get_settings()
        if not settings.mercado_livre_access_token:
            raise StorePaused(
                "Mercado Livre API needs MERCADO_LIVRE_ACCESS_TOKEN. "
                "Affiliate IDs only monetize links; they do not authorize product search."
            )

        terms = [(keyword, "hardware") for keyword in keywords] if keywords else list(HARDWARE_QUERIES)
        per_query_limit = max(3, min(10, limit // max(len(terms), 1) + 1))
        snapshots: list[ProductSnapshot] = []
        seen: set[str] = set()

        for query, category_slug in terms:
            payload = await self._search(query, per_query_limit, settings.mercado_livre_access_token)
            for item in payload.get("results", []):
                snapshot = self._parse_item(item, category_slug)
                if snapshot is None or snapshot.external_id in seen:
                    continue
                seen.add(snapshot.external_id)
                snapshots.append(snapshot)
                if len(snapshots) >= limit:
                    return snapshots
        return snapshots

    async def _search(self, query: str, limit: int, access_token: str) -> dict:
        await self._sleep_for_rate_limit()
        url = f"{self.base_url}/sites/MLB/search"
        headers = self._headers() | {"Authorization": f"Bearer {access_token}"}
        params = {"q": query, "limit": limit, "sort": "relevance"}
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, params=params, headers=headers)
        if response.status_code in {401, 403}:
            raise StorePaused("Mercado Livre API rejected the access token. Check MERCADO_LIVRE_ACCESS_TOKEN.")
        self._handle_status(response)
        return response.json()

    def _parse_item(self, item: dict, category_slug: str) -> ProductSnapshot | None:
        item_id = item.get("id")
        title = item.get("title")
        price = item.get("price")
        permalink = item.get("permalink")
        if not item_id or not title or price is None or not permalink:
            return None

        original_price = item.get("original_price")
        if original_price is not None and original_price <= price:
            original_price = None

        thumbnail = item.get("thumbnail") or item.get("secure_thumbnail")
        if thumbnail:
            thumbnail = thumbnail.replace("http://", "https://")

        available_quantity = item.get("available_quantity")
        stock_status = "in_stock" if available_quantity is None or available_quantity > 0 else "out_of_stock"
        shipping = item.get("shipping") or {}
        seller = item.get("seller") or {}

        return ProductSnapshot(
            store_slug=self.store_slug,
            external_id=str(item_id),
            sku=str(item_id),
            title=str(title),
            url=str(permalink),
            current_price=float(price),
            old_price=float(original_price) if original_price else None,
            stock_status=stock_status,
            image_url=thumbnail,
            category_slug=category_slug,
            seller_name=str(seller.get("nickname")) if seller.get("nickname") else None,
            seller_reputation=str(seller.get("power_seller_status")) if seller.get("power_seller_status") else None,
            shipping_price=0 if shipping.get("free_shipping") else None,
            raw_payload=item,
        )
