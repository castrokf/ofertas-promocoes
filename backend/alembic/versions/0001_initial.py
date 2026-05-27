from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _create_table_once(table_name: str, *columns, **kwargs) -> None:
    if not _table_exists(table_name):
        op.create_table(table_name, *columns, **kwargs)


def _create_index_once(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    if not _table_exists(table_name):
        return
    inspector = sa.inspect(op.get_bind())
    existing_indexes = {index["name"] for index in inspector.get_indexes(table_name)}
    existing_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}
    if index_name not in existing_indexes and index_name not in existing_constraints:
        op.create_index(index_name, table_name, columns, unique=unique)


def _create_unique_constraint_once(constraint_name: str, table_name: str, columns: list[str]) -> None:
    if not _table_exists(table_name):
        return
    inspector = sa.inspect(op.get_bind())
    existing_constraints = {constraint["name"] for constraint in inspector.get_unique_constraints(table_name)}
    if constraint_name not in existing_constraints:
        op.create_unique_constraint(constraint_name, table_name, columns)


def _drop_table_once(table_name: str) -> None:
    if _table_exists(table_name):
        op.drop_table(table_name)


def upgrade() -> None:
    _create_table_once(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_users_email", "users", ["email"], unique=True)

    _create_table_once(
        "stores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("collect_method", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("supports_affiliate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="1"),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_stores_name", "stores", ["name"], unique=True)
    _create_index_once("ix_stores_slug", "stores", ["slug"], unique=True)

    _create_table_once(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_discount_percent", sa.Float(), nullable=False, server_default="15"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_categories_name", "categories", ["name"], unique=True)
    _create_index_once("ix_categories_slug", "categories", ["slug"], unique=True)

    _create_table_once(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("normalized_title", sa.String(length=500), nullable=False),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("store_id", "external_id", name="uq_products_store_external_id"),
    )
    _create_index_once("ix_products_store_id", "products", ["store_id"])
    _create_index_once("ix_products_category_id", "products", ["category_id"])
    _create_index_once("ix_products_external_id", "products", ["external_id"])
    _create_index_once("ix_products_sku", "products", ["sku"])
    _create_index_once("ix_products_title", "products", ["title"])
    _create_index_once("ix_products_normalized_title", "products", ["normalized_title"])

    _create_table_once(
        "price_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("old_price", sa.Float(), nullable=True),
        sa.Column("pix_price", sa.Float(), nullable=True),
        sa.Column("card_price", sa.Float(), nullable=True),
        sa.Column("boleto_price", sa.Float(), nullable=True),
        sa.Column("shipping_price", sa.Float(), nullable=True),
        sa.Column("stock_status", sa.String(length=80), nullable=False, server_default="unknown"),
        sa.Column("checked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("raw_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    _create_index_once("ix_price_history_product_id", "price_history", ["product_id"])
    _create_index_once("ix_price_history_checked_at", "price_history", ["checked_at"])

    _create_table_once(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("price_history_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("price_history.id"), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("quality_label", sa.String(length=80), nullable=False, server_default="normal"),
        sa.Column("score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("current_price", sa.Float(), nullable=False),
        sa.Column("old_price", sa.Float(), nullable=True),
        sa.Column("discount_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("historical_low", sa.Float(), nullable=True),
        sa.Column("avg_7d", sa.Float(), nullable=True),
        sa.Column("avg_30d", sa.Float(), nullable=True),
        sa.Column("avg_90d", sa.Float(), nullable=True),
        sa.Column("decision_reasons", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("affiliate_url", sa.Text(), nullable=True),
        sa.Column("requires_manual_approval", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_deals_product_id", "deals", ["product_id"])
    _create_index_once("ix_deals_status", "deals", ["status"])

    _create_table_once(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("min_discount_percent", sa.Float(), nullable=False, server_default="15"),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("max_shipping_price", sa.Float(), nullable=True),
        sa.Column("cooldown_hours", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("auto_publish", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    _create_table_once(
        "publish_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("channel_type", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_unique_constraint_once("uq_publish_channels_name", "publish_channels", ["name"])

    _create_table_once(
        "publications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("deal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("deals.id"), nullable=False),
        sa.Column("channel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("publish_channels.id"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("published_url", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_publications_deal_id", "publications", ["deal_id"])
    _create_index_once("ix_publications_channel_id", "publications", ["channel_id"])

    _create_table_once(
        "affiliate_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("affiliate_url", sa.Text(), nullable=False),
        sa.Column("is_monetized", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("utm_source", sa.String(length=120), nullable=True),
        sa.Column("click_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_affiliate_links_store_id", "affiliate_links", ["store_id"])

    _create_table_once(
        "monitored_urls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("store_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("collect_frequency_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_monitored_urls_store_id", "monitored_urls", ["store_id"])

    _create_table_once(
        "log_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    _create_index_once("ix_log_entries_level", "log_entries", ["level"])
    _create_index_once("ix_log_entries_source", "log_entries", ["source"])
    _create_index_once("ix_log_entries_created_at", "log_entries", ["created_at"])

    _create_table_once(
        "system_settings",
        sa.Column("key", sa.String(length=160), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    for table_name in [
        "system_settings",
        "log_entries",
        "monitored_urls",
        "affiliate_links",
        "publications",
        "publish_channels",
        "alert_rules",
        "deals",
        "price_history",
        "products",
        "categories",
        "stores",
        "users",
    ]:
        _drop_table_once(table_name)
