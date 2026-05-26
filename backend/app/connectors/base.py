from __future__ import annotations

import asyncio
import hashlib
import logging
import random
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus
from urllib.robotparser import RobotFileParser

import httpx


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ProductSnapshot:
    store_slug: str
    external_id: str
    title: str
    url: str
    current_price: float
    old_price: float | None = None
    pix_price: float | None = None
    card_price: float | None = None
    boleto_price: float | None = None
    shipping_price: float | None = None
    stock_status: str = "unknown"
    image_url: str | None = None
    category_slug: str | None = None
    sku: str | None = None
    brand: str | None = None
    seller_name: str | None = None
    seller_reputation: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class ConnectorError(Exception):
    pass


class StorePaused(ConnectorError):
    pass


class BaseConnector:
    store_slug = "base"
    store_name = "Base"
    base_url = ""
    collect_method = "public_page"
    default_categories: tuple[str, ...] = ()
    rate_limit_per_minute = 20

    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds
        self._robots_cache: dict[str, RobotFileParser | None] = {}

    async def collect(self, keywords: list[str] | None = None, limit: int = 50) -> list[ProductSnapshot]:
        raise NotImplementedError

    async def _sleep_for_rate_limit(self) -> None:
        delay = max(60 / max(self.rate_limit_per_minute, 1), 0.5)
        await asyncio.sleep(delay + random.uniform(0, 0.6))

    async def _fetch_json(self, url: str) -> Any:
        await self._sleep_for_rate_limit()
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers=self._headers())
        self._handle_status(response)
        return response.json()

    async def _fetch_html(self, url: str) -> str:
        if not self._robots_can_fetch(url):
            raise StorePaused(f"robots.txt blocks {url}")
        await self._sleep_for_rate_limit()
        async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, headers=self._headers())
        self._handle_status(response)
        return response.text

    def _handle_status(self, response: httpx.Response) -> None:
        if response.status_code in {401, 403, 429, 503}:
            raise StorePaused(f"{self.store_name} paused after HTTP {response.status_code}")
        response.raise_for_status()

    def _robots_can_fetch(self, url: str) -> bool:
        if not self.base_url:
            return True
        robots_url = self.base_url.rstrip("/") + "/robots.txt"
        parser = self._robots_cache.get(robots_url)
        if robots_url not in self._robots_cache:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            try:
                parser.read()
            except Exception:
                logger.info("Could not read robots.txt for %s; continuing cautiously.", self.store_slug)
                parser = None
            self._robots_cache[robots_url] = parser
        return True if parser is None else parser.can_fetch(self._headers()["User-Agent"], url)

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": "AutoTechDealsX/2.0 respectful deal monitor",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
        }

    @staticmethod
    def query(value: str) -> str:
        return quote_plus(value.strip())

    @staticmethod
    def stable_external_id(store_slug: str, url: str, title: str) -> str:
        digest = hashlib.sha256(f"{store_slug}|{url}|{title}".lower().encode("utf-8")).hexdigest()
        return digest[:32]
