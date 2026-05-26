from __future__ import annotations

from config import Settings
from scrapers.base import HtmlListingScraper


class AliExpressScraper(HtmlListingScraper):
    store_name = "AliExpress"
    base_url = "https://pt.aliexpress.com"
    segment = "hardware"
    search_url_template = "https://pt.aliexpress.com/w/wholesale-{query}.html"
    listing_selectors = ('a[href*="/item/"]', '[class*="search-card-item"]')
    title_selectors = ("h3", "h1", '[class*="multi--title"]')
    price_selectors = ('[class*="price-sale"]', '[class*="multi--price-sale"]', '[class*="price"]')
    old_price_selectors = ('[class*="price-original"]', '[class*="line-through"]')
    link_selectors = ("a[href]",)
    image_selectors = ("img",)
    stock_selectors = ('[class*="item-status"]',)
    discount_selectors = ('[class*="discount"]',)
    shipping_selectors = ('[class*="delivery"]',)

    def absolute_url(self, href: str) -> str:
        if href.startswith("//"):
            return f"https:{href}"
        return super().absolute_url(href)


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return AliExpressScraper(settings).collect_deals(categories)
