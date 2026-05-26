from __future__ import annotations

import httpx

from app.publishers.base import BasePublisher, PublishPayload, PublishResult


class DiscordPublisher(BasePublisher):
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def publish(self, payload: PublishPayload) -> PublishResult:
        if not self.webhook_url:
            return PublishResult(success=False, error="Discord webhook not configured")
        body = {"content": payload.text}
        if payload.embed:
            body["embeds"] = [payload.embed]
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.webhook_url, json=body)
        if response.status_code >= 300:
            return PublishResult(success=False, error=f"Discord HTTP {response.status_code}: {response.text}")
        return PublishResult(success=True)
