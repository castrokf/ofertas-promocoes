from __future__ import annotations

from app.services.message_service import MessageInput, MessageService


class AICaptionGenerator:
    """Optional AI wrapper. It never invents facts; fallback is deterministic."""

    def __init__(self, enabled: bool = False, api_key: str = "") -> None:
        self.enabled = enabled and bool(api_key)
        self.api_key = api_key
        self.fallback = MessageService()

    async def generate(self, channel: str, data: MessageInput) -> str:
        # Hook point for a provider SDK. Keep factual fields locked to DB values.
        if channel == "telegram":
            return self.fallback.telegram(data)
        return self.fallback.twitter(data)
