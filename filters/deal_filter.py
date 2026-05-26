from __future__ import annotations

import math
import re
from urllib.parse import urlsplit, urlunsplit

from config import POPULAR_BRANDS, POPULAR_GAME_KEYWORDS, Settings
from database.db import make_product_hash
from database.models import PriceHistorySummary, ProductDeal
from filters.category_filter import categorize_title, detect_segment, normalize_text


SUSPICIOUS_TITLE_PATTERNS = (
    "generico",
    "replica",
    "similar a",
    "compativel com",
    "open box",
    "usado",
    "sucata",
    "sem caixa",
    "lote",
    "misteriosa",
)


def parse_price(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    raw = normalize_text(str(value))
    match = re.findall(r"\d+[.,]?\d*", raw.replace(".", "").replace(",", "."))
    if not match:
        return None
    try:
        return float(match[0])
    except ValueError:
        return None


def clean_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))


def calculate_discount(old_price: float | None, current_price: float | None) -> float:
    if not old_price or not current_price or old_price <= 0 or current_price >= old_price:
        return 0.0
    return round(((old_price - current_price) / old_price) * 100, 2)


def normalize_product_data(raw_product: dict, store: str | None = None) -> ProductDeal | None:
    title = re.sub(r"\s+", " ", str(raw_product.get("title", "")).strip())
    url = str(raw_product.get("url", "")).strip()
    current_price = parse_price(raw_product.get("current_price") or raw_product.get("price"))
    old_price = parse_price(raw_product.get("old_price") or raw_product.get("list_price"))
    discount = raw_product.get("discount_percent")
    discount_percent = (
        float(discount)
        if isinstance(discount, (int, float))
        else calculate_discount(old_price, current_price)
    )
    stock_status = normalize_text(str(raw_product.get("stock_status", "unknown")))
    detected_store = store or str(raw_product.get("store", "")).strip()
    segment = str(raw_product.get("segment", "")).strip() or detect_segment(
        detected_store,
        str(raw_product.get("category", "")),
    )
    category = str(raw_product.get("category", "")).strip() or categorize_title(title, segment)

    if not title or not url or current_price is None or not detected_store:
        return None

    product_url = clean_url(url)
    product_hash = make_product_hash(detected_store, product_url, title)
    metadata = dict(raw_product.get("metadata") or {})

    return ProductDeal(
        title=title[:160],
        category=category,
        store=detected_store,
        current_price=current_price,
        old_price=old_price,
        discount_percent=round(discount_percent, 2),
        url=product_url,
        affiliate_url=str(raw_product.get("affiliate_url", "")).strip(),
        image_url=str(raw_product.get("image_url", "")).strip(),
        stock_status=stock_status or "unknown",
        segment=segment,
        product_hash=product_hash,
        metadata=metadata,
    )


def _is_suspicious_title(title: str) -> bool:
    normalized = normalize_text(title)
    return any(pattern in normalized for pattern in SUSPICIOUS_TITLE_PATTERNS)


def _is_stock_available(stock_status: str) -> bool:
    normalized = normalize_text(stock_status)
    blocked = {"sem estoque", "out of stock", "indisponivel", "sold out", "esgotado"}
    return normalized not in blocked


def _has_abusive_shipping(product: ProductDeal) -> bool:
    shipping_cost = parse_price(product.metadata.get("shipping_cost"))
    shipping_text = normalize_text(str(product.metadata.get("shipping_text", "")))
    if shipping_text and any(term in shipping_text for term in {"a combinar", "consulte"}):
        return True
    if shipping_cost is None:
        return False
    return shipping_cost > (product.current_price * 0.25)


def _is_store_allowed(settings: Settings, store: str) -> bool:
    return store in settings.allowed_stores


def _looks_like_marketplace_risk(product: ProductDeal) -> bool:
    seller_name = normalize_text(str(product.metadata.get("seller", "")))
    if product.store != "Mercado Livre":
        return False
    if not seller_name:
        return True
    trusted_sellers = {
        "kabum",
        "pichau",
        "loja oficial",
        "amazon brasil",
        "terabyte",
        "mercado livre official store",
    }
    return not any(token in seller_name for token in trusted_sellers)


def is_good_deal(
    product: ProductDeal,
    settings: Settings,
    history: PriceHistorySummary,
    already_posted: bool = False,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []

    if already_posted:
        reasons.append("produto ja postado anteriormente")
    if not _is_store_allowed(settings, product.store):
        reasons.append("loja fora da lista permitida")
    if _is_suspicious_title(product.title):
        reasons.append("titulo suspeito ou generico")
    if not _is_stock_available(product.stock_status):
        reasons.append("produto sem estoque")
    if product.discount_percent < settings.min_discount_percent:
        reasons.append("desconto abaixo do minimo")
    if (
        already_posted
        and history.previous_price is not None
        and product.current_price >= history.previous_price
    ):
        reasons.append("preco nao esta menor que o ultimo salvo")
    if _has_abusive_shipping(product):
        reasons.append("frete abusivo identificado")
    if _looks_like_marketplace_risk(product):
        reasons.append("marketplace sem vendedor confiavel")

    return not reasons, reasons


def score_deal(
    product: ProductDeal,
    history: PriceHistorySummary,
    settings: Settings,
) -> float:
    score = product.discount_percent * 3

    normalized_title = normalize_text(product.title)
    if any(brand in normalized_title for brand in POPULAR_BRANDS):
        score += 15
    if any(keyword in normalized_title for keyword in POPULAR_GAME_KEYWORDS):
        score += 15
    if history.is_new_low:
        score += 18
    if history.lowest_price is not None and product.current_price <= history.lowest_price:
        score += 8
    if not history.has_history:
        score -= 5

    rating = product.metadata.get("rating")
    if isinstance(rating, (int, float)):
        score += min(float(rating), 100) / 5

    popularity = product.metadata.get("popularity")
    if isinstance(popularity, (int, float)):
        score += math.log1p(float(popularity))

    if product.segment == "games" and "gratis" in normalize_text(product.category):
        score += 20

    return round(score, 2)
