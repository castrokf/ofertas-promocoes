from __future__ import annotations

from celery import Celery

from app.core.config import get_settings


settings = get_settings()

celery_app = Celery(
    "autotechdealsx",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    beat_schedule={
        "collect-priority-products-every-minute": {
            "task": "app.workers.tasks.collect_priority_products",
            "schedule": 60,
        },
        "collect-common-categories-every-five-minutes": {
            "task": "app.workers.tasks.collect_common_categories",
            "schedule": 300,
        },
        "collect-games-every-fifteen-minutes": {
            "task": "app.workers.tasks.collect_games",
            "schedule": 900,
        },
        "refresh-price-history-every-thirty-minutes": {
            "task": "app.workers.tasks.refresh_price_history",
            "schedule": 1800,
        },
        "publish-approved-deals-every-minute": {
            "task": "app.workers.tasks.publish_approved_deals",
            "schedule": 60,
        },
    },
)
