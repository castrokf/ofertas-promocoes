from __future__ import annotations

import logging

from config import Settings
from scrapers.base import BaseScraper, ScraperSkipped


logger = logging.getLogger(__name__)


class EpicScraper(BaseScraper):
    store_name = "Epic Games Store"
    base_url = "https://store.epicgames.com"
    segment = "games"
    free_games_url = (
        "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        "?locale=pt-BR&country=BR&allowCountries=BR"
    )

    @staticmethod
    def _best_image_url(item: dict) -> str:
        preferred_types = ("OfferImageWide", "DieselStoreFrontWide", "featuredMedia", "Thumbnail")
        images = item.get("keyImages", [])
        for image_type in preferred_types:
            for image in images:
                if image.get("type") == image_type and image.get("url"):
                    return image["url"]
        return next((image.get("url") for image in images if image.get("url")), "")

    def collect_deals(self, categories: list[str] | None = None) -> list[dict]:
        try:
            payload = self.fetch_json(self.free_games_url)
        except ScraperSkipped as exc:
            logger.warning("Epic Games Store pausado neste ciclo: %s", exc)
            return []
        except Exception as exc:
            logger.exception("Falha ao consultar a Epic: %s", exc)
            return []
        if not isinstance(payload, dict):
            return []

        elements = (
            payload.get("data", {})
            .get("Catalog", {})
            .get("searchStore", {})
            .get("elements", [])
        )
        deals: list[dict] = []

        for item in elements[:20]:
            title = item.get("title")
            slug = item.get("productSlug") or item.get("urlSlug")
            if not title or not slug:
                continue
            promotions = item.get("promotions") or {}
            current_price = (
                item.get("price", {})
                .get("totalPrice", {})
                .get("discountPrice")
            )
            original_price = (
                item.get("price", {})
                .get("totalPrice", {})
                .get("originalPrice")
            )
            if current_price is None:
                continue
            deals.append(
                {
                    "title": title,
                    "category": "jogos gratis temporarios" if current_price == 0 else "jogos em promocao",
                    "store": self.store_name,
                    "price": current_price / 100,
                    "old_price": (original_price / 100) if original_price else None,
                    "url": f"{self.base_url}/pt-BR/p/{slug}",
                    "image_url": self._best_image_url(item),
                    "stock_status": "digital",
                    "segment": self.segment,
                    "metadata": {
                        "promotions": promotions,
                    },
                }
            )
        return deals


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return EpicScraper(settings).collect_deals(categories)
