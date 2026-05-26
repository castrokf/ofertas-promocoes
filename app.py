from __future__ import annotations

import logging
import os
import time
from dataclasses import asdict
from threading import Lock
from typing import Any

from flask import Flask, jsonify, redirect, render_template, request, url_for

from affiliate.generic_affiliate import generate_affiliate_link
from config import Settings, setup_logging
from database.db import DatabaseManager
from filters.deal_filter import is_good_deal, normalize_product_data, score_deal
from filters.price_history import check_price_history
from main import _scraper_plan
from publisher.post_generator import generate_tweet_text
from scrapers import SCRAPER_REGISTRY


logger = logging.getLogger(__name__)

app = Flask(__name__)
setup_logging()

_cache_lock = Lock()
_cache: dict[str, Any] = {
    "segment": "",
    "generated_at": 0.0,
    "deals": [],
    "stats": {},
    "errors": [],
}


def _settings_for_web() -> Settings:
    settings = Settings.from_env()
    settings.test_mode = True
    settings.db_path = settings.test_db_path
    return settings


def _format_brl(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _parse_limit(raw_limit: str | None, default: int = 24) -> int:
    try:
        return max(1, min(int(raw_limit or default), 60))
    except ValueError:
        return default


def _collect_raw_deals(settings: Settings, segment: str) -> tuple[list[dict], list[str]]:
    raw_deals: list[dict] = []
    errors: list[str] = []

    for store_name, categories in _scraper_plan(settings, segment):
        scraper_fn = SCRAPER_REGISTRY[store_name]
        try:
            raw_deals.extend(scraper_fn(settings, categories))
        except Exception as exc:
            logger.exception("Falha ao coletar %s no painel web.", store_name)
            errors.append(f"{store_name}: {exc}")

    return raw_deals, errors


def _build_dashboard_data(segment: str, limit: int) -> dict[str, Any]:
    settings = _settings_for_web()
    db = DatabaseManager(settings.db_path)
    raw_deals, errors = _collect_raw_deals(settings, segment)

    approved: list[tuple[Any, Any, float]] = []
    seen_urls: set[str] = set()
    rejected = 0

    for raw in raw_deals:
        product = normalize_product_data(raw)
        if product is None or product.url in seen_urls:
            continue
        seen_urls.add(product.url)
        history = check_price_history(db, product.product_hash, product.current_price)
        already_posted = db.has_been_posted(product.product_hash)
        product.affiliate_url = generate_affiliate_link(product, settings)
        ok, _reasons = is_good_deal(product, settings, history, already_posted=already_posted)
        db.upsert_product(product)
        db.add_price_history(product.product_hash, product.current_price)

        if not ok:
            rejected += 1
            continue

        approved.append((product, history, score_deal(product, history, settings)))

    approved.sort(key=lambda item: item[2], reverse=True)
    selected = approved[:limit]
    deals = []

    for product, history, score in selected:
        tweet_text = generate_tweet_text(product, history)
        deals.append(
            {
                "title": product.title,
                "category": product.category,
                "store": product.store,
                "segment": product.segment,
                "current_price": _format_brl(product.current_price),
                "old_price": _format_brl(product.old_price),
                "discount_percent": int(round(product.discount_percent)),
                "url": product.url,
                "affiliate_url": product.affiliate_url or product.url,
                "image_url": product.image_url,
                "stock_status": product.stock_status,
                "score": score,
                "tweet_text": tweet_text,
                "history": asdict(history),
            }
        )

    return {
        "segment": segment,
        "generated_at": time.time(),
        "deals": deals,
        "stats": {
            "collected": len(raw_deals),
            "approved": len(approved),
            "shown": len(deals),
            "rejected": rejected,
        },
        "errors": errors,
    }


def get_dashboard_data(segment: str, limit: int, force_refresh: bool = False) -> dict[str, Any]:
    ttl_seconds = int(os.getenv("WEB_CACHE_TTL_SECONDS", "600"))
    now = time.time()

    with _cache_lock:
        cache_fresh = now - float(_cache["generated_at"] or 0) < ttl_seconds
        cache_matches = _cache["segment"] == segment and len(_cache["deals"]) >= min(limit, 1)
        if not force_refresh and cache_fresh and cache_matches:
            return {
                **_cache,
                "deals": _cache["deals"][:limit],
            }

        data = _build_dashboard_data(segment=segment, limit=limit)
        _cache.update(data)
        return data


@app.get("/")
def index():
    segment = request.args.get("segment", "games")
    if segment not in {"games", "hardware", "all"}:
        segment = "games"
    limit = _parse_limit(request.args.get("limit"))
    force_refresh = request.args.get("refresh") == "1"
    data = get_dashboard_data(segment=segment, limit=limit, force_refresh=force_refresh)
    generated_at = time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(data["generated_at"]))
    return render_template(
        "dashboard.html",
        segment=segment,
        limit=limit,
        generated_at=generated_at,
        deals=data["deals"],
        stats=data["stats"],
        errors=data["errors"],
    )


@app.post("/refresh")
def refresh():
    segment = request.form.get("segment", "games")
    limit = request.form.get("limit", "24")
    return redirect(url_for("index", segment=segment, limit=limit, refresh="1"))


@app.get("/api/deals")
def api_deals():
    segment = request.args.get("segment", "games")
    if segment not in {"games", "hardware", "all"}:
        segment = "games"
    limit = _parse_limit(request.args.get("limit"))
    force_refresh = request.args.get("refresh") == "1"
    return jsonify(get_dashboard_data(segment=segment, limit=limit, force_refresh=force_refresh))


@app.get("/healthz")
def healthz():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)
