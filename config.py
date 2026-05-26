from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "autotechdealsx.log"
DB_FILE = BASE_DIR / "autotechdealsx.sqlite3"
TEST_DB_FILE = BASE_DIR / "autotechdealsx_test.sqlite3"
EXPORT_DIR = BASE_DIR / "exports"

DEFAULT_HEADERS = {
    "User-Agent": (
        "AutoTechDealsX/1.0 (+https://example.invalid/bot-info; "
        "respectful monitoring for promotions)"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

HARDWARE_CATEGORIES = [
    "placas de video",
    "processadores",
    "memoria ram",
    "ssd",
    "monitores gamer",
    "teclados",
    "mouses",
    "headsets",
    "cadeiras gamer",
    "notebooks gamer",
    "consoles",
    "controles",
    "acessorios gamer",
]

GAME_CATEGORIES = [
    "jogos em promocao",
    "jogos gratis temporarios",
    "bundles",
    "dlcs",
    "pre-vendas com desconto",
    "cupons ativos",
]

POPULAR_BRANDS = {
    "nvidia",
    "amd",
    "intel",
    "asus",
    "msi",
    "gigabyte",
    "kingston",
    "corsair",
    "logitech",
    "razer",
    "hyperx",
    "steelseries",
    "sony",
    "microsoft",
    "xbox",
    "playstation",
    "nintendo",
    "lenovo",
    "acer",
    "dell",
    "samsung",
    "lg",
    "aoc",
}

POPULAR_GAME_KEYWORDS = {
    "elden ring",
    "cyberpunk",
    "baldur",
    "resident evil",
    "forza",
    "fifa",
    "ea sports fc",
    "god of war",
    "red dead",
    "gta",
    "hades",
    "hollow knight",
    "persona",
    "zelda",
    "mario",
}


def _get_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_csv(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(slots=True)
class Settings:
    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""
    x_bearer_token: str = ""
    amazon_associate_tag: str = ""
    aliexpress_affiliate_id: str = ""
    mercadolivre_affiliate_id: str = ""
    mercadolivre_tool_id: str = ""
    post_interval_minutes: int = 15
    max_posts_per_hour: int = 4
    min_discount_percent: int = 15
    test_mode: bool = True
    request_timeout: int = 20
    min_request_delay_seconds: float = 1.5
    max_request_delay_seconds: float = 4.5
    max_title_length: int = 160
    disabled_stores: tuple[str, ...] = ()
    db_path: Path = DB_FILE
    test_db_path: Path = TEST_DB_FILE
    export_dir: Path = EXPORT_DIR
    log_path: Path = LOG_FILE
    hardware_categories: list[str] = field(default_factory=lambda: list(HARDWARE_CATEGORIES))
    game_categories: list[str] = field(default_factory=lambda: list(GAME_CATEGORIES))
    allowed_stores: tuple[str, ...] = (
        "Amazon Brasil",
        "KaBuM",
        "Terabyte",
        "Pichau",
        "Mercado Livre",
        "AliExpress",
        "Nuuvem",
        "Steam",
        "Epic Games Store",
        "GOG",
        "Green Man Gaming",
        "Xbox Store",
        "PlayStation Store",
        "Nintendo eShop",
    )

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(BASE_DIR / ".env")
        LOG_DIR.mkdir(exist_ok=True)
        return cls(
            x_api_key=os.getenv("X_API_KEY", ""),
            x_api_secret=os.getenv("X_API_SECRET", ""),
            x_access_token=os.getenv("X_ACCESS_TOKEN", ""),
            x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
            x_bearer_token=os.getenv("X_BEARER_TOKEN", ""),
            amazon_associate_tag=os.getenv("AMAZON_ASSOCIATE_TAG", ""),
            aliexpress_affiliate_id=os.getenv("ALIEXPRESS_AFFILIATE_ID", ""),
            mercadolivre_affiliate_id=os.getenv("MERCADO_LIVRE_AFFILIATE_ID", ""),
            mercadolivre_tool_id=os.getenv("MERCADO_LIVRE_TOOL_ID", ""),
            post_interval_minutes=_get_int(os.getenv("POST_INTERVAL_MINUTES"), 15),
            max_posts_per_hour=_get_int(os.getenv("MAX_POSTS_PER_HOUR"), 4),
            min_discount_percent=_get_int(os.getenv("MIN_DISCOUNT_PERCENT"), 15),
            test_mode=_get_bool(os.getenv("TEST_MODE"), True),
            disabled_stores=_get_csv(os.getenv("DISABLED_STORES")),
        )


def setup_logging(log_path: Path | None = None) -> None:
    destination = log_path or LOG_FILE
    destination.parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(destination, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
