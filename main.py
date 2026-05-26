from __future__ import annotations

import argparse
import logging
import math
from collections import Counter
from datetime import datetime

from affiliate.generic_affiliate import generate_affiliate_link
from config import Settings, setup_logging
from database.db import DatabaseManager
from database.models import ExecutionStats, PriceHistorySummary, ProductDeal
from filters.deal_filter import is_good_deal, normalize_product_data, score_deal
from filters.price_history import check_price_history
from publisher.manual_exporter import export_ready_posts
from publisher.post_generator import generate_tweet_text
from publisher.twitter_publisher import publish_to_x
from scheduler.jobs import render_status_panel, run_scheduler
from scrapers import SCRAPER_REGISTRY


logger = logging.getLogger(__name__)


def configure_runtime_settings(settings: Settings) -> Settings:
    if settings.test_mode:
        settings.db_path = settings.test_db_path
    return settings


def _select_segment(args: argparse.Namespace) -> str:
    if args.hardware and args.games:
        raise SystemExit("Use apenas um segmento por vez: --hardware ou --games.")
    if args.hardware:
        return "hardware"
    if args.games:
        return "games"
    return "all"


def _scraper_plan(settings: Settings, segment: str) -> list[tuple[str, list[str]]]:
    hardware_plan = [
        ("Amazon Brasil", settings.hardware_categories),
        ("KaBuM", settings.hardware_categories),
        ("Terabyte", settings.hardware_categories),
        ("Pichau", settings.hardware_categories),
        ("Mercado Livre", settings.hardware_categories),
        ("AliExpress", settings.hardware_categories),
    ]
    games_plan = [
        ("Nuuvem", settings.game_categories),
        ("Steam", settings.game_categories),
        ("Epic Games Store", settings.game_categories),
        ("GOG", settings.game_categories),
    ]
    if segment == "hardware":
        plan = hardware_plan
    elif segment == "games":
        plan = games_plan
    else:
        plan = hardware_plan + games_plan

    disabled = set(settings.disabled_stores)
    if disabled:
        logger.info("Lojas desativadas por configuracao: %s", ", ".join(sorted(disabled)))
    return [(store, categories) for store, categories in plan if store not in disabled]


def collect_all_deals(
    settings: Settings,
    segment: str = "all",
    stats: ExecutionStats | None = None,
) -> list[ProductDeal]:
    collected: list[ProductDeal] = []
    seen_links: set[str] = set()

    for store_name, categories in _scraper_plan(settings, segment):
        scraper_fn = SCRAPER_REGISTRY[store_name]
        try:
            raw_deals = scraper_fn(settings, categories)
        except Exception as exc:
            logger.exception("Falha ao coletar ofertas em %s: %s", store_name, exc)
            if stats is not None:
                stats.errors.append(f"{store_name}: {exc}")
            continue

        if stats is not None:
            stats.offers_collected += len(raw_deals)

        for raw in raw_deals:
            product = normalize_product_data(raw, store_name)
            if product is None or product.url in seen_links:
                continue
            seen_links.add(product.url)
            collected.append(product)

    return collected


def _posts_allowed_this_cycle(settings: Settings, db: DatabaseManager) -> int:
    recent_posts = db.get_recent_post_count(within_hours=1)
    remaining_quota = max(0, settings.max_posts_per_hour - recent_posts)
    per_cycle = max(
        1,
        math.ceil((settings.max_posts_per_hour * settings.post_interval_minutes) / 60),
    )
    return min(remaining_quota, per_cycle)


def _prepare_deals(
    settings: Settings,
    db: DatabaseManager,
    products: list[ProductDeal],
) -> list[tuple[ProductDeal, PriceHistorySummary, float]]:
    approved: list[tuple[ProductDeal, PriceHistorySummary, float]] = []
    rejection_reasons: Counter[str] = Counter()

    for product in products:
        history = check_price_history(db, product.product_hash, product.current_price)
        already_posted = db.has_been_posted(product.product_hash)
        product.affiliate_url = generate_affiliate_link(product, settings)
        ok, reasons = is_good_deal(product, settings, history, already_posted=already_posted)

        db.upsert_product(product)
        db.add_price_history(product.product_hash, product.current_price)

        if not ok:
            rejection_reasons.update(reasons)
            logger.debug("Oferta rejeitada [%s]: %s", product.store, "; ".join(reasons))
            continue

        deal_score = score_deal(product, history, settings)
        approved.append((product, history, deal_score))

    if rejection_reasons:
        summary = "; ".join(
            f"{reason}: {count}" for reason, count in rejection_reasons.most_common()
        )
        logger.info("Resumo das ofertas rejeitadas: %s", summary)

    approved.sort(key=lambda item: item[2], reverse=True)
    return approved


def _publish_best_deals(
    settings: Settings,
    db: DatabaseManager,
    approved_deals: list[tuple[ProductDeal, PriceHistorySummary, float]],
    stats: ExecutionStats,
) -> None:
    allowed_posts = _posts_allowed_this_cycle(settings, db)
    if allowed_posts <= 0:
        logger.info("Limite horario de posts atingido.")
        return

    for product, history, _score in approved_deals[:allowed_posts]:
        tweet_text = generate_tweet_text(product, history)
        result = publish_to_x(tweet_text, settings, dry_run=settings.test_mode)
        if result.error:
            logger.error("Falha ao publicar %s: %s", product.title, result.error)
            stats.errors.append(result.error)
            continue
        if result.published:
            db.save_posted_deal(
                product_hash=product.product_hash,
                title=product.title,
                store=product.store,
                posted_url=result.posted_url,
                tweet_id=result.tweet_id,
            )
            stats.offers_posted += 1
            logger.info("Oferta publicada: %s", product.title)
        else:
            logger.info("Preview de tweet gerado para %s:\n%s", product.title, tweet_text)


def _export_best_deals(
    settings: Settings,
    approved_deals: list[tuple[ProductDeal, PriceHistorySummary, float]],
    export_limit: int | None = None,
) -> None:
    if not approved_deals:
        logger.info("Nenhuma oferta aprovada para exportar.")
        return
    max_posts = export_limit or settings.max_posts_per_hour
    output_path = export_ready_posts(
        approved_deals=approved_deals,
        output_dir=settings.export_dir,
        max_posts=max_posts,
    )
    logger.info("Posts prontos exportados para: %s", output_path)


def process_once(
    settings: Settings,
    db: DatabaseManager,
    segment: str,
    stats: ExecutionStats | None = None,
    export_only: bool = False,
    export_limit: int | None = None,
) -> ExecutionStats:
    current_stats = stats or ExecutionStats()
    current_stats.last_run_started_at = current_stats.last_run_started_at or datetime.now()

    products = collect_all_deals(settings=settings, segment=segment, stats=current_stats)
    approved = _prepare_deals(settings=settings, db=db, products=products)
    current_stats.offers_approved = len(approved)
    if export_only:
        _export_best_deals(settings=settings, approved_deals=approved, export_limit=export_limit)
    else:
        _publish_best_deals(settings=settings, db=db, approved_deals=approved, stats=current_stats)
    current_stats.last_run_finished_at = datetime.now()
    return current_stats


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AutoTechDealsX")
    parser.add_argument("--test", action="store_true", help="Executa em modo teste.")
    parser.add_argument("--run", action="store_true", help="Executa continuamente.")
    parser.add_argument("--once", action="store_true", help="Executa uma unica vez.")
    parser.add_argument("--export", action="store_true", help="Gera posts prontos em arquivo sem publicar.")
    parser.add_argument("--export-limit", type=int, default=None, help="Quantidade maxima de posts exportados.")
    parser.add_argument("--hardware", action="store_true", help="Somente ofertas de hardware.")
    parser.add_argument("--games", action="store_true", help="Somente ofertas de jogos digitais.")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    segment = _select_segment(args)

    settings = Settings.from_env()
    if args.test:
        settings.test_mode = True
    configure_runtime_settings(settings)

    setup_logging(settings.log_path)
    db = DatabaseManager(settings.db_path)

    try:
        if args.run:
            run_scheduler(
                settings=settings,
                job_callable=lambda stats: process_once(
                    settings,
                    db,
                    segment,
                    stats,
                    export_only=args.export,
                    export_limit=args.export_limit,
                ),
                segment=segment,
            )
            return

        stats = process_once(
            settings=settings,
            db=db,
            segment=segment,
            export_only=args.export,
            export_limit=args.export_limit,
        )
        stats.next_run_at = None
        render_status_panel(
            stats=stats,
            mode="export" if args.export else "test" if settings.test_mode else "once",
            segment=segment,
        )
    except KeyboardInterrupt:
        logger.info("Execucao interrompida pelo usuario.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
