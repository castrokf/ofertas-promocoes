from __future__ import annotations

from config import Settings
from scrapers.base import HtmlListingScraper


class NuuvemScraper(HtmlListingScraper):
    store_name = "Nuuvem"
    base_url = "https://www.nuuvem.com"
    segment = "games"
    search_url_template = "https://www.nuuvem.com/br-pt/catalog/page/1/search/{query}"
    listing_selectors = ("article.product-card", ".product-card", "a.product-card--wrapper")
    title_selectors = (".product-title", "h3", "span")
    price_selectors = (".product-button__label", ".price", ".product-price")
    old_price_selectors = (".product-old-price", ".price-old")
    link_selectors = ("a[href]",)
    image_selectors = ("img",)
    stock_selectors = (".product-available",)
    discount_selectors = (".label-discount",)


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return NuuvemScraper(settings).collect_deals(categories)
