from __future__ import annotations

import logging

from app.connectors.base import BaseConnector, ProductSnapshot


logger = logging.getLogger(__name__)


class SteamConnector(BaseConnector):
    store_slug = "steam"
    store_name = "Steam"
    base_url = "https://store.steampowered.com"
    collect_method = "api"
    rate_limit_per_minute = 30
    featured_url = "https://store.steampowered.com/api/featuredcategories?cc=br&l=portuguese"

    async def collect(self, keywords: list[str] | None = None, limit: int = 50) -> list[ProductSnapshot]:
        payload = await self._fetch_json(self.featured_url)
        snapshots: list[ProductSnapshot] = []
        for section in ("specials", "top_sellers", "new_releases"):
            items = payload.get(section, {}).get("items", [])
            for item in items:
                appid = str(item.get("id"))
                final_price = item.get("final_price")
                if final_price is None or not appid:
                    continue
                original_price = item.get("original_price")
                snapshots.append(
                    ProductSnapshot(
                        store_slug=self.store_slug,
                        external_id=appid,
                        title=item.get("name") or f"Steam App {appid}",
                        url=f"{self.base_url}/app/{appid}",
                        current_price=round(final_price / 100, 2),
                        old_price=round(original_price / 100, 2) if original_price else None,
                        stock_status="in_stock",
                        image_url=item.get("large_capsule_image"),
                        category_slug="jogos-digitais",
                        raw_payload=item,
                    )
                )
                if len(snapshots) >= limit:
                    return snapshots
        return snapshots
