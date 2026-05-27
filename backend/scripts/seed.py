from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import PASSWORD_ALGORITHM, hash_password
from app.models import (
    Category,
    ChannelType,
    PublishChannel,
    Store,
    StoreCollectMethod,
    StoreStatus,
    User,
)


STORES = [
    ("Amazon", "amazon", "https://www.amazon.com.br", StoreCollectMethod.affiliate_feed),
    ("Mercado Livre", "mercado-livre", "https://www.mercadolivre.com.br", StoreCollectMethod.api),
    ("AliExpress", "aliexpress", "https://www.aliexpress.com", StoreCollectMethod.affiliate_feed),
    ("Magazine Luiza", "magazine-luiza", "https://www.magazineluiza.com.br", StoreCollectMethod.affiliate_feed),
    ("Shopee", "shopee", "https://shopee.com.br", StoreCollectMethod.affiliate_feed),
    ("Kabum", "kabum", "https://www.kabum.com.br", StoreCollectMethod.public_page),
    ("Terabyte", "terabyte", "https://www.terabyteshop.com.br", StoreCollectMethod.public_page),
    ("Pichau", "pichau", "https://www.pichau.com.br", StoreCollectMethod.public_page),
    ("Steam", "steam", "https://store.steampowered.com", StoreCollectMethod.api),
    ("Nuuvem", "nuuvem", "https://www.nuuvem.com", StoreCollectMethod.affiliate_feed),
    ("Epic Games Store", "epic-games", "https://store.epicgames.com", StoreCollectMethod.api),
    ("Green Man Gaming", "green-man-gaming", "https://www.greenmangaming.com", StoreCollectMethod.affiliate_feed),
    ("GOG", "gog", "https://www.gog.com", StoreCollectMethod.api),
    ("Xbox Store", "xbox-store", "https://www.xbox.com", StoreCollectMethod.api),
    ("PlayStation Store", "playstation-store", "https://store.playstation.com", StoreCollectMethod.api),
    ("Nintendo eShop", "nintendo-eshop", "https://www.nintendo.com", StoreCollectMethod.api),
]

CATEGORIES = [
    ("Placas de Video", "placas-de-video"),
    ("Processadores", "processadores"),
    ("Placas-Mae", "placas-mae"),
    ("Memoria RAM", "memoria-ram"),
    ("SSD", "ssd"),
    ("HD", "hd"),
    ("Fontes", "fontes"),
    ("Gabinetes", "gabinetes"),
    ("Coolers", "coolers"),
    ("Water Coolers", "water-coolers"),
    ("Monitores", "monitores"),
    ("Notebooks", "notebooks"),
    ("Cadeiras Gamer", "cadeiras-gamer"),
    ("Teclados", "teclados"),
    ("Mouses", "mouses"),
    ("Headsets", "headsets"),
    ("Controles", "controles"),
    ("Jogos Digitais", "jogos-digitais"),
    ("Bundles", "bundles"),
    ("Gift Cards", "gift-cards"),
]


def seed() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == settings.admin_email))
        if admin is None:
            db.add(
                User(
                    email=settings.admin_email,
                    hashed_password=hash_password(settings.admin_password),
                    is_admin=True,
                )
            )
        elif settings.reset_admin_password_on_start or not admin.hashed_password.startswith(f"{PASSWORD_ALGORITHM}$"):
            admin.hashed_password = hash_password(settings.admin_password)
            admin.is_admin = True
            admin.is_active = True

        for name, slug, base_url, method in STORES:
            if db.scalar(select(Store).where(Store.slug == slug)) is None:
                db.add(
                    Store(
                        name=name,
                        slug=slug,
                        base_url=base_url,
                        collect_method=method,
                        status=StoreStatus.active,
                        supports_affiliate=slug
                        in {"amazon", "mercado-livre", "aliexpress", "magazine-luiza", "shopee"},
                        trust_score=1.0,
                    )
                )

        for name, slug in CATEGORIES:
            if db.scalar(select(Category).where(Category.slug == slug)) is None:
                db.add(Category(name=name, slug=slug, min_discount_percent=15))

        if db.scalar(select(PublishChannel).where(PublishChannel.name == "Site")) is None:
            db.add(PublishChannel(name="Site", channel_type=ChannelType.site, config={}, is_active=True))

        db.commit()


if __name__ == "__main__":
    seed()
    settings = get_settings()
    print(f"Seed completed. Admin: {settings.admin_email}")
