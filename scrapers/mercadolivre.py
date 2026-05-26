from __future__ import annotations

from config import Settings
from scrapers.base import HtmlListingScraper


class MercadoLivreScraper(HtmlListingScraper):
    store_name = "Mercado Livre"
    base_url = "https://lista.mercadolivre.com.br"
    segment = "hardware"
    search_url_template = "https://lista.mercadolivre.com.br/{query}"
    listing_selectors = (".ui-search-result",)
    title_selectors = (".poly-component__title", "h2")
    price_selectors = (".andes-money-amount__fraction", ".price-tag-fraction")
    old_price_selectors = (".andes-money-amount--previous .andes-money-amount__fraction", "s")
    link_selectors = ("a[href]",)
    image_selectors = ("img",)
    stock_selectors = (".ui-search-item__group__element",)
    discount_selectors = (".andes-money-amount__discount",)
    seller_selectors = (".poly-component__seller", ".poly-component__brand")
    shipping_selectors = (".poly-shipping__text",)

    def parse_listing_node(self, node, category: str):
        item = super().parse_listing_node(node, category)
        if item:
            item["metadata"]["seller"] = item["metadata"].get("seller") or "unknown"
        return item


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return MercadoLivreScraper(settings).collect_deals(categories)
