from __future__ import annotations

import re
import unicodedata


CATEGORY_KEYWORDS = {
    "placas de video": ["rtx", "rx ", "radeon", "geforce", "gpu", "placa de video"],
    "processadores": ["ryzen", "core i", "threadripper", "processador", "cpu"],
    "memoria ram": ["memoria", "ddr4", "ddr5", "ram ", "so-dimm"],
    "ssd": ["ssd", "nvme", "m.2", "sata"],
    "monitores gamer": ["monitor", "hz", "ultrawide", "ips", "oled"],
    "teclados": ["teclado", "keyboard", "switch blue", "switch red", "mecanico"],
    "mouses": ["mouse", "dpi", "wireless mouse"],
    "headsets": ["headset", "fone gamer", "headphone gamer"],
    "cadeiras gamer": ["cadeira gamer", "ergonomica", "cadeira office"],
    "notebooks gamer": ["notebook gamer", "laptop gamer"],
    "consoles": ["playstation", "xbox series", "nintendo switch", "console"],
    "controles": ["controle", "joystick", "dualsense", "xbox wireless controller"],
    "acessorios gamer": ["mousepad", "webcam", "dock", "suporte", "captura", "stream deck"],
    "jogos em promocao": ["game", "jogo", "edition", "goty", "deluxe edition", "standard edition"],
    "jogos gratis temporarios": ["100% off", "free now", "gratis", "gratutio", "free game"],
    "bundles": ["bundle", "pack", "collection", "trilogy"],
    "dlcs": ["dlc", "expansion", "season pass", "add-on"],
    "pre-vendas com desconto": ["pre-venda", "preorder", "pre-order"],
    "cupons ativos": ["cupom", "coupon", "codigo"],
}

GAME_STORES = {
    "Nuuvem",
    "Steam",
    "Epic Games Store",
    "GOG",
    "Green Man Gaming",
    "Xbox Store",
    "PlayStation Store",
    "Nintendo eShop",
}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def categorize_title(title: str, segment_hint: str | None = None) -> str:
    haystack = normalize_text(title)
    best_match = "ofertas gerais" if segment_hint != "games" else "jogos em promocao"
    best_score = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in haystack)
        if score > best_score:
            best_match = category
            best_score = score

    return best_match


def detect_segment(store: str, category: str | None = None) -> str:
    if store in GAME_STORES:
        return "games"
    normalized_category = normalize_text(category or "")
    if normalized_category in {
        "jogos em promocao",
        "jogos gratis temporarios",
        "bundles",
        "dlcs",
        "pre-vendas com desconto",
        "cupons ativos",
    }:
        return "games"
    return "hardware"
