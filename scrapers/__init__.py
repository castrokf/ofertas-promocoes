from scrapers.aliexpress import collect_deals as collect_aliexpress_deals
from scrapers.amazon import collect_deals as collect_amazon_deals
from scrapers.epic import collect_deals as collect_epic_deals
from scrapers.gog import collect_deals as collect_gog_deals
from scrapers.kabum import collect_deals as collect_kabum_deals
from scrapers.mercadolivre import collect_deals as collect_mercadolivre_deals
from scrapers.nuuvem import collect_deals as collect_nuuvem_deals
from scrapers.pichau import collect_deals as collect_pichau_deals
from scrapers.steam import collect_deals as collect_steam_deals
from scrapers.terabyte import collect_deals as collect_terabyte_deals

SCRAPER_REGISTRY = {
    "Amazon Brasil": collect_amazon_deals,
    "KaBuM": collect_kabum_deals,
    "Terabyte": collect_terabyte_deals,
    "Pichau": collect_pichau_deals,
    "Mercado Livre": collect_mercadolivre_deals,
    "AliExpress": collect_aliexpress_deals,
    "Nuuvem": collect_nuuvem_deals,
    "Steam": collect_steam_deals,
    "Epic Games Store": collect_epic_deals,
    "GOG": collect_gog_deals,
}

__all__ = ["SCRAPER_REGISTRY"]
