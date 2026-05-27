from __future__ import annotations

import logging

from app.connectors.base import BaseConnector, ProductSnapshot


logger = logging.getLogger(__name__)


class PreparedConnector(BaseConnector):
    """Safe placeholder for stores that need an official API/feed or allowed parser."""

    legal_note = "Configure official API, affiliate feed, RSS or an allowed public parser before enabling collection."

    async def collect(self, keywords: list[str] | None = None, limit: int = 50) -> list[ProductSnapshot]:
        logger.info("%s connector is prepared but not enabled. %s", self.store_name, self.legal_note)
        return []


class AmazonConnector(PreparedConnector):
    store_slug = "amazon"
    store_name = "Amazon"
    base_url = "https://www.amazon.com.br"
    collect_method = "affiliate_feed"


class AliExpressConnector(PreparedConnector):
    store_slug = "aliexpress"
    store_name = "AliExpress"
    base_url = "https://www.aliexpress.com"
    collect_method = "affiliate_feed"


class MagazineLuizaConnector(PreparedConnector):
    store_slug = "magazine-luiza"
    store_name = "Magazine Luiza"
    base_url = "https://www.magazineluiza.com.br"
    collect_method = "affiliate_feed"


class ShopeeConnector(PreparedConnector):
    store_slug = "shopee"
    store_name = "Shopee"
    base_url = "https://shopee.com.br"
    collect_method = "affiliate_feed"


class KabumConnector(PreparedConnector):
    store_slug = "kabum"
    store_name = "Kabum"
    base_url = "https://www.kabum.com.br"
    collect_method = "public_page"


class TerabyteConnector(PreparedConnector):
    store_slug = "terabyte"
    store_name = "Terabyte"
    base_url = "https://www.terabyteshop.com.br"
    collect_method = "public_page"


class PichauConnector(PreparedConnector):
    store_slug = "pichau"
    store_name = "Pichau"
    base_url = "https://www.pichau.com.br"
    collect_method = "public_page"


class NuuvemConnector(PreparedConnector):
    store_slug = "nuuvem"
    store_name = "Nuuvem"
    base_url = "https://www.nuuvem.com"
    collect_method = "affiliate_feed"


class GreenManGamingConnector(PreparedConnector):
    store_slug = "green-man-gaming"
    store_name = "Green Man Gaming"
    base_url = "https://www.greenmangaming.com"
    collect_method = "affiliate_feed"


class GOGConnector(PreparedConnector):
    store_slug = "gog"
    store_name = "GOG"
    base_url = "https://www.gog.com"
    collect_method = "api"


class EpicGamesConnector(PreparedConnector):
    store_slug = "epic-games"
    store_name = "Epic Games Store"
    base_url = "https://store.epicgames.com"
    collect_method = "api"


class XboxStoreConnector(PreparedConnector):
    store_slug = "xbox-store"
    store_name = "Xbox Store"
    base_url = "https://www.xbox.com"
    collect_method = "api"


class PlaystationStoreConnector(PreparedConnector):
    store_slug = "playstation-store"
    store_name = "PlayStation Store"
    base_url = "https://store.playstation.com"
    collect_method = "api"


class NintendoEshopConnector(PreparedConnector):
    store_slug = "nintendo-eshop"
    store_name = "Nintendo eShop"
    base_url = "https://www.nintendo.com"
    collect_method = "api"
