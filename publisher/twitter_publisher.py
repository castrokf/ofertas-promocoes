from __future__ import annotations

import logging

from config import Settings
from database.models import PublishResult


logger = logging.getLogger(__name__)


def _credentials_ready(settings: Settings) -> bool:
    return all(
        [
            settings.x_api_key,
            settings.x_api_secret,
            settings.x_access_token,
            settings.x_access_token_secret,
        ]
    )


def publish_to_x(tweet_text: str, settings: Settings, dry_run: bool = False) -> PublishResult:
    if dry_run or settings.test_mode:
        logger.info("Modo teste ativo. Tweet gerado sem publicacao: %s", tweet_text)
        return PublishResult(
            published=False,
            text=tweet_text,
            tweet_id=None,
            posted_url=None,
        )

    if not _credentials_ready(settings):
        return PublishResult(
            published=False,
            error="Credenciais do X incompletas para publicacao real.",
            text=tweet_text,
        )

    try:
        import tweepy
    except ImportError as exc:
        return PublishResult(
            published=False,
            error=f"Tweepy nao instalado: {exc}",
            text=tweet_text,
        )

    try:
        client = tweepy.Client(
            bearer_token=settings.x_bearer_token or None,
            consumer_key=settings.x_api_key,
            consumer_secret=settings.x_api_secret,
            access_token=settings.x_access_token,
            access_token_secret=settings.x_access_token_secret,
        )
        response = client.create_tweet(text=tweet_text, user_auth=True)
        tweet_id = str(response.data["id"])
        posted_url = f"https://x.com/i/web/status/{tweet_id}"
        logger.info("Tweet publicado com sucesso: %s", tweet_id)
        return PublishResult(
            published=True,
            tweet_id=tweet_id,
            posted_url=posted_url,
            text=tweet_text,
        )
    except tweepy.Forbidden as exc:
        error = (
            "X recusou a publicacao com 403. Verifique no X Developer Console se "
            "o app esta com User authentication/OAuth 1.0a em Read and write e "
            "gere novos Access Token e Access Token Secret depois de salvar a permissao."
        )
        logger.error("%s Detalhe: %s", error, exc)
        return PublishResult(
            published=False,
            error=error,
            text=tweet_text,
        )
    except Exception as exc:  # pragma: no cover - depende de API externa
        logger.exception("Falha ao publicar no X.")
        return PublishResult(
            published=False,
            error=str(exc),
            text=tweet_text,
        )
