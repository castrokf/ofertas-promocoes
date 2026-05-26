from __future__ import annotations

import logging

from config import Settings
from scrapers.base import BaseScraper, ScraperSkipped


logger = logging.getLogger(__name__)


class SteamScraper(BaseScraper):
    store_name = "Steam"
    base_url = "https://store.steampowered.com"
    segment = "games"
    featured_url = "https://store.steampowered.com/api/featuredcategories?cc=br&l=portuguese"

    def collect_deals(self, categories: list[str] | None = None) -> list[dict]:
        try:
            payload = self.fetch_json(self.featured_url)
        except ScraperSkipped as exc:
            logger.warning("Steam pausado neste ciclo: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Falha ao consultar a Steam: %s", exc)
            return []
        if not isinstance(payload, dict):
            return []

        deals: list[dict] = []
        sections = ["specials", "top_sellers", "new_releases"]
        for section in sections:
            items = payload.get(section, {}).get("items", [])
            for item in items[:12]:
                final_price = item.get("final_price")
                initial_price = item.get("original_price")
                if final_price is None:
                    continue
                appid = item.get("id")
                title = item.get("name") or f"Steam App {appid}"
                deals.append(
                    {
                        "title": title,
                        "category": "jogos gratis temporarios"
                        if final_price == 0
                        else "jogos em promocao",
                        "store": self.store_name,
                        "price": final_price / 100,
                        "old_price": (initial_price / 100) if initial_price else None,
                        "discount_percent": item.get("discount_percent"),
                        "url": f"{self.base_url}/app/{appid}",
                        "image_url": item.get("large_capsule_image"),
                        "stock_status": "digital",
                        "segment": self.segment,
                        "metadata": {
                            "popularity": item.get("review_count", 0),
                        },
                    }
                )
        return deals


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return SteamScraper(settings).collect_deals(categories)
