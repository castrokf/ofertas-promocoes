from __future__ import annotations

import logging
import random
import re
import time
from typing import Iterable
from urllib.parse import quote_plus, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup, Tag
from requests import HTTPError

from config import DEFAULT_HEADERS, Settings


logger = logging.getLogger(__name__)


class ScraperSkipped(Exception):
    """Base exception for expected scraper skips."""


class RobotsBlocked(ScraperSkipped):
    """Raised when robots.txt disallows the requested URL."""


class StoreTemporarilyUnavailable(ScraperSkipped):
    """Raised when a store asks us to slow down or blocks automated access."""


class BaseScraper:
    store_name = ""
    base_url = ""
    segment = "hardware"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers.update({"User-Agent": DEFAULT_HEADERS["User-Agent"]})
        self._robots_cache: dict[str, RobotFileParser | None] = {}

    def delay(self) -> None:
        time.sleep(
            random.uniform(
                self.settings.min_request_delay_seconds,
                self.settings.max_request_delay_seconds,
            )
        )

    def can_fetch(self, url: str) -> bool:
        parsed = urlsplit(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        if robots_url in self._robots_cache:
            parser = self._robots_cache[robots_url]
            return True if parser is None else parser.can_fetch(DEFAULT_HEADERS["User-Agent"], url)

        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
            self._robots_cache[robots_url] = parser
            return parser.can_fetch(DEFAULT_HEADERS["User-Agent"], url)
        except Exception:
            logger.info("Nao foi possivel validar robots.txt em %s; seguindo com cautela.", robots_url)
            self._robots_cache[robots_url] = None
            return True

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        try:
            response.raise_for_status()
        except HTTPError as exc:
            status_code = response.status_code
            if status_code in {401, 403, 429, 503}:
                raise StoreTemporarilyUnavailable(
                    f"HTTP {status_code} em {response.url}"
                ) from exc
            raise

    def fetch_html(self, url: str) -> BeautifulSoup | None:
        if not self.can_fetch(url):
            raise RobotsBlocked(f"robots.txt bloqueou {url}")
        self.delay()
        response = self.session.get(url, timeout=self.settings.request_timeout)
        self._raise_for_status(response)
        return BeautifulSoup(response.text, "html.parser")

    def fetch_json(self, url: str) -> dict | list | None:
        if not self.can_fetch(url):
            raise RobotsBlocked(f"robots.txt bloqueou {url}")
        self.delay()
        response = self.session.get(url, timeout=self.settings.request_timeout)
        self._raise_for_status(response)
        return response.json()

    def absolute_url(self, href: str) -> str:
        return urljoin(self.base_url, href)

    @staticmethod
    def query_term(term: str) -> str:
        return quote_plus(term.strip())

    @staticmethod
    def first_text(node: Tag, selectors: Iterable[str]) -> str:
        for selector in selectors:
            found = node.select_one(selector)
            if found:
                text = " ".join(found.stripped_strings)
                if text:
                    return text
        return ""

    @staticmethod
    def first_attr(node: Tag, selectors: Iterable[str], attr_names: Iterable[str]) -> str:
        for selector in selectors:
            found = node.select_one(selector)
            if not found:
                continue
            for attr in attr_names:
                value = found.get(attr)
                if value:
                    return str(value)
        return ""

    @staticmethod
    def extract_discount(text: str) -> float | None:
        match = re.search(r"(\d{1,3})\s*%", text or "")
        if not match:
            return None
        return float(match.group(1))


class HtmlListingScraper(BaseScraper):
    search_url_template = ""
    listing_selectors: tuple[str, ...] = ()
    title_selectors: tuple[str, ...] = ()
    price_selectors: tuple[str, ...] = ()
    old_price_selectors: tuple[str, ...] = ()
    link_selectors: tuple[str, ...] = ()
    image_selectors: tuple[str, ...] = ()
    stock_selectors: tuple[str, ...] = ()
    discount_selectors: tuple[str, ...] = ()
    seller_selectors: tuple[str, ...] = ()
    shipping_selectors: tuple[str, ...] = ()
    max_items_per_category = 10

    def search_url(self, category: str) -> str:
        return self.search_url_template.format(query=self.query_term(category))

    def get_listing_nodes(self, soup: BeautifulSoup) -> list[Tag]:
        for selector in self.listing_selectors:
            nodes = soup.select(selector)
            if nodes:
                return nodes
        return []

    def parse_listing_node(self, node: Tag, category: str) -> dict | None:
        title = self.first_text(node, self.title_selectors)
        current_price = self.first_text(node, self.price_selectors)
        old_price = self.first_text(node, self.old_price_selectors)
        link = self.first_attr(node, self.link_selectors, ("href",))
        image_url = self.first_attr(node, self.image_selectors, ("src", "data-src", "srcset"))
        stock_status = self.first_text(node, self.stock_selectors) or "in_stock"
        discount_text = self.first_text(node, self.discount_selectors)
        seller = self.first_text(node, self.seller_selectors)
        shipping_text = self.first_text(node, self.shipping_selectors)

        if not title or not current_price or not link:
            return None

        if image_url and " " in image_url and image_url.startswith("http"):
            image_url = image_url.split(" ")[0]

        return {
            "title": title,
            "category": category,
            "store": self.store_name,
            "price": current_price,
            "old_price": old_price,
            "discount_percent": self.extract_discount(discount_text) if discount_text else None,
            "url": self.absolute_url(link),
            "image_url": image_url,
            "stock_status": stock_status,
            "segment": self.segment,
            "metadata": {
                "seller": seller,
                "shipping_text": shipping_text,
            },
        }

    def collect_deals(self, categories: list[str]) -> list[dict]:
        deals: list[dict] = []
        seen_urls: set[str] = set()

        for category in categories:
            url = self.search_url(category)
            try:
                soup = self.fetch_html(url)
            except RobotsBlocked:
                logger.info(
                    "%s pulado neste ciclo: robots.txt nao permite a rota de busca.",
                    self.store_name,
                )
                break
            except StoreTemporarilyUnavailable as exc:
                logger.warning(
                    "%s pausado neste ciclo: %s. Nao vamos insistir para evitar bloqueio.",
                    self.store_name,
                    exc,
                )
                break
            except requests.RequestException as exc:
                logger.warning(
                    "Falha temporaria no scraper %s para %s: %s",
                    self.store_name,
                    category,
                    exc,
                )
                continue
            except Exception as exc:
                logger.exception(
                    "Falha inesperada no scraper %s para %s: %s",
                    self.store_name,
                    category,
                    exc,
                )
                continue
            if soup is None:
                continue

            for node in self.get_listing_nodes(soup)[: self.max_items_per_category]:
                item = self.parse_listing_node(node, category)
                if not item or item["url"] in seen_urls:
                    continue
                seen_urls.add(item["url"])
                deals.append(item)

        return deals
