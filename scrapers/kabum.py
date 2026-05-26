from __future__ import annotations

from config import Settings
from scrapers.base import HtmlListingScraper


class KabumScraper(HtmlListingScraper):
    store_name = "KaBuM"
    base_url = "https://www.kabum.com.br"
    segment = "hardware"
    search_url_template = "https://www.kabum.com.br/busca/{query}"
    listing_selectors = ("article", '[class*="productCard"]')
    title_selectors = ('[class*="nameCard"]', "h2", "h3", "a[title]")
    price_selectors = ('[class*="priceCard"]', '[class*="finalPrice"]', '[class*="price"]')
    old_price_selectors = ('[class*="oldPrice"]', "s")
    link_selectors = ("a[href]",)
    image_selectors = ("img",)
    stock_selectors = ('[class*="available"]', '[class*="stock"]')
    discount_selectors = ('[class*="discount"]',)


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return KabumScraper(settings).collect_deals(categories)
