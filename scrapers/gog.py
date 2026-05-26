from __future__ import annotations

import logging

from config import Settings
from scrapers.base import BaseScraper, ScraperSkipped


logger = logging.getLogger(__name__)


class GOGScraper(BaseScraper):
    store_name = "GOG"
    base_url = "https://www.gog.com"
    segment = "games"
    deals_url = (
        "https://www.gog.com/games/ajax/filtered"
        "?mediaType=game&sort=popularity&page=1&price=discounted"
    )

    def collect_deals(self, categories: list[str] | None = None) -> list[dict]:
        try:
            payload = self.fetch_json(self.deals_url)
        except ScraperSkipped as exc:
            logger.warning("GOG pausado neste ciclo: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Falha ao consultar a GOG: %s", exc)
            return []
        if not isinstance(payload, dict):
            return []

        products = payload.get("products", [])
        deals: list[dict] = []
        for item in products[:20]:
            title = item.get("title")
            url = item.get("url")
            current_price = item.get("price", {}).get("finalAmount")
            if not title or current_price is None or not url:
                continue
            deals.append(
                {
                    "title": title,
                    "category": "jogos em promocao",
                    "store": self.store_name,
                    "price": current_price,
                    "old_price": item.get("price", {}).get("baseAmount"),
                    "discount_percent": item.get("price", {}).get("discountPercentage"),
                    "url": self.absolute_url(url),
                    "image_url": item.get("image"),
                    "stock_status": "digital",
                    "segment": self.segment,
                    "metadata": {
                        "rating": item.get("rating", 0),
                    },
                }
            )
        return deals


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return GOGScraper(settings).collect_deals(categories)
