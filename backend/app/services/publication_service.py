from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import ChannelType, Deal, DealStatus, Publication, PublicationStatus, PublishChannel
from app.publishers.base import PublishPayload
from app.publishers.discord import DiscordPublisher
from app.publishers.telegram import TelegramPublisher
from app.publishers.twitter_x import TwitterXPublisher
from app.services.log_service import LogService
from app.services.message_service import MessageInput, MessageService


class PublicationService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.messages = MessageService()
        self.logs = LogService(db)

    async def publish_deal(self, deal: Deal, channel: PublishChannel) -> Publication:
        product = deal.product
        store = product.store
        category_slug = product.category.slug if product.category else None
        data = MessageInput(
            title=product.title,
            store=store.name,
            current_price=deal.current_price,
            old_price=deal.old_price,
            discount_percent=deal.discount_percent,
            quality_label=deal.quality_label,
            link=deal.affiliate_url or product.url,
            category=category_slug,
        )
        text = self._message_for_channel(channel, data)
        embed = self.messages.discord_embed(data, product.image_url) if channel.channel_type == ChannelType.discord else None
        payload = PublishPayload(text=text, title=product.title, url=deal.affiliate_url or product.url, image_url=product.image_url, embed=embed)
        if self.settings.publish_dry_run:
            result = DryRunPublisher().publish_sync(payload)
        else:
            result = await self._publisher_for(channel).publish(payload)

        publication = Publication(
            deal_id=deal.id,
            channel_id=channel.id,
            status=self._publication_status(result.success),
            message_text=text,
            external_id=result.external_id,
            published_url=result.published_url,
            attempt_count=1,
            error_message=result.error,
            published_at=datetime.now(timezone.utc) if result.success else None,
        )
        self.db.add(publication)
        if result.success and not self.settings.publish_dry_run:
            deal.status = DealStatus.published
        self.logs.record(
            "info" if result.success else "error",
            f"publisher:{channel.channel_type.value}",
            "Publication processed",
            {"deal_id": str(deal.id), "channel_id": str(channel.id), "dry_run": self.settings.publish_dry_run, "error": result.error},
        )
        self.db.commit()
        self.db.refresh(publication)
        return publication

    def _message_for_channel(self, channel: PublishChannel, data: MessageInput) -> str:
        if channel.channel_type == ChannelType.telegram:
            return self.messages.telegram(data)
        return self.messages.twitter(data)

    def _publisher_for(self, channel: PublishChannel):
        if channel.channel_type == ChannelType.discord:
            return DiscordPublisher(channel.config.get("webhook_url") or self.settings.discord_webhook_url)
        if channel.channel_type == ChannelType.telegram:
            return TelegramPublisher(
                channel.config.get("bot_token") or self.settings.telegram_bot_token,
                channel.config.get("chat_id") or self.settings.telegram_chat_id,
            )
        if channel.channel_type == ChannelType.twitter_x:
            return TwitterXPublisher(self.settings)
        return SitePublisher()

    def _publication_status(self, success: bool) -> PublicationStatus:
        if self.settings.publish_dry_run:
            return PublicationStatus.skipped
        return PublicationStatus.success if success else PublicationStatus.failed


class SitePublisher:
    async def publish(self, payload: PublishPayload):
        from app.publishers.base import PublishResult

        return PublishResult(success=True, published_url=payload.url)


class DryRunPublisher:
    def publish_sync(self, payload: PublishPayload):
        from app.publishers.base import PublishResult

        return PublishResult(success=True, published_url=payload.url, error="dry run: external publish skipped")
