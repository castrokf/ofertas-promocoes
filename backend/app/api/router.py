from fastapi import APIRouter

from app.api.routes import auth, categories, channels, deals, health, logs, metrics, monitored_urls, rules, stores


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(stores.router, prefix="/stores", tags=["stores"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(deals.router, prefix="/deals", tags=["deals"])
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(monitored_urls.router, prefix="/monitored-urls", tags=["monitored-urls"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
