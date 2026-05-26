from __future__ import annotations

import httpx

from app.publishers.base import BasePublisher, PublishPayload, PublishResult


class TelegramPublisher(BasePublisher):
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def publish(self, payload: PublishPayload) -> PublishResult:
        if not self.bot_token or not self.chat_id:
            return PublishResult(success=False, error="Telegram token/chat not configured")
        endpoint = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        body = {
            "chat_id": self.chat_id,
            "text": payload.text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(endpoint, json=body)
        data = response.json()
        if response.status_code >= 300 or not data.get("ok"):
            return PublishResult(success=False, error=f"Telegram error: {data}")
        return PublishResult(success=True, external_id=str(data["result"]["message_id"]))
