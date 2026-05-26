from __future__ import annotations

from config import Settings
from scrapers.base import HtmlListingScraper


class AmazonScraper(HtmlListingScraper):
    store_name = "Amazon Brasil"
    base_url = "https://www.amazon.com.br"
    segment = "hardware"
    search_url_template = "https://www.amazon.com.br/s?k={query}"
    listing_selectors = ('div.s-result-item[data-component-type="s-search-result"]',)
    title_selectors = ("h2 span",)
    price_selectors = (".a-price .a-offscreen",)
    old_price_selectors = (".a-text-price .a-offscreen",)
    link_selectors = ("h2 a",)
    image_selectors = ("img.s-image",)
    stock_selectors = (".a-color-price",)
    discount_selectors = ("span.a-letter-space + span",)


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return AmazonScraper(settings).collect_deals(categories)
