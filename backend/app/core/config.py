from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AutoTechDealsX"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    public_base_url: str = "http://localhost:5173"

    database_url: str = "postgresql+psycopg://autotech:autotech@postgres:5432/autotechdealsx"
    redis_url: str = "redis://redis:6379/0"

    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 12
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    publish_mode: Literal["automatic", "semi_automatic"] = "semi_automatic"
    publish_dry_run: bool = True
    cron_secret: str = ""
    min_discount_percent: float = 15
    max_shipping_ratio: float = 0.25
    repost_cooldown_hours: int = 12
    excellent_discount_percent: float = 35
    incredible_discount_percent: float = 50
    price_error_drop_percent: float = 70

    disabled_stores: list[str] = Field(default_factory=list)
    default_rate_limit_per_minute: int = 20
    web_cache_ttl_seconds: int = 600

    amazon_associate_tag: str = ""
    mercado_livre_affiliate_id: str = ""
    mercado_livre_tool_id: str = ""
    aliexpress_affiliate_id: str = ""

    discord_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""
    x_bearer_token: str = ""

    openai_api_key: str = ""
    ai_enabled: bool = False

    @field_validator("cors_origins", "disabled_stores", mode="before")
    @classmethod
    def parse_csv(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        if isinstance(value, str):
            value = value.strip().strip('"').strip("'")
            if value.startswith("postgres://"):
                return value.replace("postgres://", "postgresql+psycopg://", 1)
            if value.startswith("postgresql://"):
                return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
