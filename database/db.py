from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from database.models import ProductDeal


def make_product_hash(store: str, url: str, title: str) -> str:
    base = f"{store}|{url.strip().lower()}|{title.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


class DatabaseManager:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self.create_tables()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def create_tables(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT,
                    store TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    old_price REAL,
                    discount_percent REAL,
                    url TEXT NOT NULL UNIQUE,
                    affiliate_url TEXT,
                    image_url TEXT,
                    stock_status TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS posted_deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_hash TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    store TEXT NOT NULL,
                    posted_url TEXT,
                    posted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    tweet_id TEXT
                );

                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_hash TEXT NOT NULL,
                    price REAL NOT NULL,
                    checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_products_url ON products (url);
                CREATE INDEX IF NOT EXISTS idx_posted_hash ON posted_deals (product_hash);
                CREATE INDEX IF NOT EXISTS idx_price_history_hash ON price_history (product_hash);
                """
            )

    def upsert_product(self, product: ProductDeal) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO products (
                    title, category, store, current_price, old_price, discount_percent,
                    url, affiliate_url, image_url, stock_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category,
                    store = excluded.store,
                    current_price = excluded.current_price,
                    old_price = excluded.old_price,
                    discount_percent = excluded.discount_percent,
                    affiliate_url = excluded.affiliate_url,
                    image_url = excluded.image_url,
                    stock_status = excluded.stock_status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    product.title,
                    product.category,
                    product.store,
                    product.current_price,
                    product.old_price,
                    product.discount_percent,
                    product.url,
                    product.affiliate_url,
                    product.image_url,
                    product.stock_status,
                ),
            )

    def add_price_history(self, product_hash: str, price: float) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO price_history (product_hash, price) VALUES (?, ?)",
                (product_hash, price),
            )

    def get_price_summary(self, product_hash: str) -> tuple[float | None, float | None]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT price
                FROM price_history
                WHERE product_hash = ?
                ORDER BY checked_at DESC, id DESC
                LIMIT 2
                """,
                (product_hash,),
            ).fetchall()
            low_row = conn.execute(
                "SELECT MIN(price) AS lowest_price FROM price_history WHERE product_hash = ?",
                (product_hash,),
            ).fetchone()

        previous_price = rows[0]["price"] if rows else None
        lowest_price = low_row["lowest_price"] if low_row else None
        return previous_price, lowest_price

    def has_been_posted(self, product_hash: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM posted_deals WHERE product_hash = ? LIMIT 1",
                (product_hash,),
            ).fetchone()
        return row is not None

    def get_recent_post_count(self, within_hours: int = 1) -> int:
        cutoff = (datetime.utcnow() - timedelta(hours=within_hours)).isoformat(sep=" ")
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS total FROM posted_deals WHERE posted_at >= ?",
                (cutoff,),
            ).fetchone()
        return int(row["total"] or 0)

    def save_posted_deal(
        self,
        product_hash: str,
        title: str,
        store: str,
        posted_url: str | None,
        tweet_id: str | None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO posted_deals (
                    product_hash, title, store, posted_url, tweet_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (product_hash, title, store, posted_url, tweet_id),
            )

    def close(self) -> None:
        return None


def save_posted_deal(
    db: DatabaseManager,
    product_hash: str,
    title: str,
    store: str,
    posted_url: str | None,
    tweet_id: str | None,
) -> None:
    db.save_posted_deal(
        product_hash=product_hash,
        title=title,
        store=store,
        posted_url=posted_url,
        tweet_id=tweet_id,
    )
