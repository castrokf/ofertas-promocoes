from __future__ import annotations

from app.core.config import Settings
from app.publishers.base import BasePublisher, PublishPayload, PublishResult


class TwitterXPublisher(BasePublisher):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def publish(self, payload: PublishPayload) -> PublishResult:
        if not all(
            [
                self.settings.x_api_key,
                self.settings.x_api_secret,
                self.settings.x_access_token,
                self.settings.x_access_token_secret,
            ]
        ):
            return PublishResult(success=False, error="X credentials not configured")
        try:
            import tweepy

            client = tweepy.Client(
                bearer_token=self.settings.x_bearer_token or None,
                consumer_key=self.settings.x_api_key,
                consumer_secret=self.settings.x_api_secret,
                access_token=self.settings.x_access_token,
                access_token_secret=self.settings.x_access_token_secret,
            )
            response = client.create_tweet(text=payload.text, user_auth=True)
            tweet_id = str(response.data["id"])
            return PublishResult(
                success=True,
                external_id=tweet_id,
                published_url=f"https://x.com/i/web/status/{tweet_id}",
            )
        except Exception as exc:
            return PublishResult(success=False, error=str(exc))
