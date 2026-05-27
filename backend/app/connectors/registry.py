from __future__ import annotations

from app.connectors.abstract_store import (
    AliExpressConnector,
    AmazonConnector,
    EpicGamesConnector,
    GOGConnector,
    GreenManGamingConnector,
    KabumConnector,
    MagazineLuizaConnector,
    NintendoEshopConnector,
    NuuvemConnector,
    PichauConnector,
    PlaystationStoreConnector,
    ShopeeConnector,
    TerabyteConnector,
    XboxStoreConnector,
)
from app.connectors.base import BaseConnector
from app.connectors.mercadolivre import MercadoLivreConnector
from app.connectors.steam import SteamConnector


CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "amazon": AmazonConnector,
    "mercado-livre": MercadoLivreConnector,
    "aliexpress": AliExpressConnector,
    "magazine-luiza": MagazineLuizaConnector,
    "shopee": ShopeeConnector,
    "kabum": KabumConnector,
    "terabyte": TerabyteConnector,
    "pichau": PichauConnector,
    "steam": SteamConnector,
    "nuuvem": NuuvemConnector,
    "green-man-gaming": GreenManGamingConnector,
    "gog": GOGConnector,
    "epic-games": EpicGamesConnector,
    "xbox-store": XboxStoreConnector,
    "playstation-store": PlaystationStoreConnector,
    "nintendo-eshop": NintendoEshopConnector,
}


def get_connector(store_slug: str) -> BaseConnector:
    connector_cls = CONNECTOR_REGISTRY[store_slug]
    return connector_cls()
