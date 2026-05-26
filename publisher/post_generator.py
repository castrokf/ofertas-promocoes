from __future__ import annotations

import random

from database.models import PriceHistorySummary, ProductDeal


HARDWARE_TEMPLATES = [
    "🔥 OFERTA TECH\n\n{title}\n💸 R$ {current_price}\n📉 {discount}% OFF\n🏪 {store}\n\n🔗 {url}\n\n{disclosure}\n\n#hardware #setupgamer #promocao",
    "🚨 PRECO BAIXOU\n\n{title}\nDe: R$ {old_price}\nPor: R$ {current_price}\n🏪 {store}\n\n🔗 {url}\n\n{disclosure}\n\n#tech #gamer #oferta",
    "⚡ DEAL GAMER\n\n{title}\n💸 R$ {current_price}\n📉 {discount}% OFF\n🏪 {store}\n\n🔗 {url}\n\n{disclosure}\n\n#pcgamer #promocao #hardware",
]

GAME_TEMPLATES = [
    "🎮 JOGO EM PROMOCAO\n\n{title}\n💸 R$ {current_price}\n📉 {discount}% OFF\n🏪 {store}\n\n🔗 {url}\n\n#games #pcgaming #promocao",
    "🕹️ GAME DEAL\n\n{title}\n💸 R$ {current_price}\n📉 {discount}% OFF\n🏪 {store}\n\n🔗 {url}\n\n#games #desconto #oferta",
    "🎯 PRECO BOM NO JOGO\n\n{title}\n💸 R$ {current_price}\n📉 {discount}% OFF\n🏪 {store}\n\n🔗 {url}\n\n#games #promocao #digital",
]

FREE_GAME_TEMPLATE = (
    "🎁 JOGO GRATIS POR TEMPO LIMITADO\n\n{title}\n💸 R$ {current_price}\n🏪 {store}\n\n🔗 {url}\n\n#freegames #games #promocao"
)


def _format_brl(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _trim_title(title: str, max_length: int) -> str:
    if len(title) <= max_length:
        return title
    return title[: max_length - 1].rstrip() + "…"


def generate_tweet_text(
    product: ProductDeal,
    history: PriceHistorySummary | None = None,
    max_length: int = 280,
) -> str:
    disclosure = ""
    if product.affiliate_url and product.affiliate_url != product.url:
        disclosure = "link afiliado / posso receber comissao"

    template_pool = HARDWARE_TEMPLATES if product.segment == "hardware" else GAME_TEMPLATES
    if "gratis" in product.category.lower():
        template = FREE_GAME_TEMPLATE
    elif history and history.previous_price and product.current_price < history.previous_price:
        template = template_pool[1 if len(template_pool) > 1 else 0]
    else:
        template = random.choice(template_pool)

    title_budget = 72 if disclosure else 88
    text = template.format(
        title=_trim_title(product.title, title_budget),
        current_price=_format_brl(product.current_price),
        old_price=_format_brl(product.old_price or history.previous_price if history else product.old_price),
        discount=int(round(product.discount_percent)),
        store=product.store,
        url=product.affiliate_url or product.url,
        disclosure=disclosure,
    )

    if len(text) <= max_length:
        return text

    reduced_title_budget = max(40, title_budget - (len(text) - max_length))
    return template.format(
        title=_trim_title(product.title, reduced_title_budget),
        current_price=_format_brl(product.current_price),
        old_price=_format_brl(product.old_price or history.previous_price if history else product.old_price),
        discount=int(round(product.discount_percent)),
        store=product.store,
        url=product.affiliate_url or product.url,
        disclosure=disclosure,
    )[:max_length]
