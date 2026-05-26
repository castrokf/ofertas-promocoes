from __future__ import annotations

from config import Settings
from scrapers.base import HtmlListingScraper


class PichauScraper(HtmlListingScraper):
    store_name = "Pichau"
    base_url = "https://www.pichau.com.br"
    segment = "hardware"
    search_url_template = "https://www.pichau.com.br/search?q={query}"
    listing_selectors = ("article", '[class*="product"]')
    title_selectors = ("h2", "h3", "a[title]")
    price_selectors = ('[class*="price"]', '[class*="finalPrice"]')
    old_price_selectors = ('[class*="oldPrice"]', "s")
    link_selectors = ("a[href]",)
    image_selectors = ("img",)
    stock_selectors = ('[class*="stock"]',)
    discount_selectors = ('[class*="discount"]',)


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return PichauScraper(settings).collect_deals(categories)
