from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MessageInput:
    title: str
    store: str
    current_price: float
    old_price: float | None
    discount_percent: float
    quality_label: str
    link: str
    pix_price: float | None = None
    category: str | None = None


def format_brl(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class MessageService:
    def twitter(self, data: MessageInput) -> str:
        badge = {
            "imperdivel": "\U0001f525 OFERTA IMPERDIVEL",
            "excelente": "\U0001f6a8 PROMOCAO ENCONTRADA",
            "boa": "\u26a1 BOA OFERTA",
            "possivel erro de preco": "\U0001f6a8 POSSIVEL ERRO DE PRECO",
        }.get(data.quality_label, "\U0001f4e2 OFERTA TECH")
        price_line = f"\U0001f4b0 {format_brl(data.pix_price or data.current_price)}"
        if data.pix_price:
            price_line += " no Pix"
        old_line = f"De {format_brl(data.old_price)} por {format_brl(data.current_price)}" if data.old_price else ""
        text = "\n".join(
            line
            for line in [
                badge,
                "",
                data.title[:96],
                old_line,
                price_line,
                f"\U0001f3ec {data.store}",
                f"\U0001f4c9 {round(data.discount_percent)}% OFF" if data.discount_percent else "",
                "",
                f"Link: {data.link}",
                "",
                "#promocao #tech #games" if data.category == "jogos-digitais" else "#hardware #promocao #setupgamer",
            ]
            if line
        )
        return text[:280]

    def telegram(self, data: MessageInput) -> str:
        return (
            f"<b>{data.quality_label.upper()}</b>\n\n"
            f"{data.title}\n"
            f"Preco: <b>{format_brl(data.pix_price or data.current_price)}</b>\n"
            f"Loja: {data.store}\n"
            f"Desconto: {round(data.discount_percent)}%\n\n"
            f"<a href=\"{data.link}\">Abrir oferta</a>"
        )

    def discord_embed(self, data: MessageInput, image_url: str | None = None) -> dict:
        return {
            "title": data.title,
            "url": data.link,
            "description": f"{data.quality_label.upper()} em {data.store}",
            "color": 0x0F766E,
            "fields": [
                {"name": "Preco", "value": format_brl(data.pix_price or data.current_price), "inline": True},
                {"name": "Desconto", "value": f"{round(data.discount_percent)}%", "inline": True},
                {"name": "Loja", "value": data.store, "inline": True},
            ],
            "image": {"url": image_url} if image_url else None,
        }
