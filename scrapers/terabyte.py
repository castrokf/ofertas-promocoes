from __future__ import annotations

from config import Settings
from scrapers.base import HtmlListingScraper


class TerabyteScraper(HtmlListingScraper):
    store_name = "Terabyte"
    base_url = "https://www.terabyteshop.com.br"
    segment = "hardware"
    search_url_template = "https://www.terabyteshop.com.br/busca?str={query}"
    listing_selectors = ("article", ".pbox", ".product-item")
    title_selectors = ("h2", "h3", ".prod-name", "a[title]")
    price_selectors = (".tbt_especial", ".price", ".prod-new-price")
    old_price_selectors = (".tbt_old", ".de", "s")
    link_selectors = ("a[href]",)
    image_selectors = ("img",)
    stock_selectors = (".stock", ".disponibilidade")
    discount_selectors = (".desconto",)


def collect_deals(settings: Settings, categories: list[str]) -> list[dict]:
    return TerabyteScraper(settings).collect_deals(categories)
