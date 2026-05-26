from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PublishPayload:
    text: str
    title: str
    url: str
    image_url: str | None = None
    embed: dict | None = None


@dataclass(slots=True)
class PublishResult:
    success: bool
    external_id: str | None = None
    published_url: str | None = None
    error: str | None = None


class BasePublisher:
    async def publish(self, payload: PublishPayload) -> PublishResult:
        raise NotImplementedError
