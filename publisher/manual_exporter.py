from __future__ import annotations

from datetime import datetime
from pathlib import Path

from database.models import PriceHistorySummary, ProductDeal
from publisher.post_generator import generate_tweet_text


ApprovedDeal = tuple[ProductDeal, PriceHistorySummary, float]


def export_ready_posts(
    approved_deals: list[ApprovedDeal],
    output_dir: Path,
    max_posts: int,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = output_dir / f"posts_ready_{timestamp}.txt"
    selected_deals = approved_deals[:max_posts]

    lines = [
        "AutoTechDealsX - posts prontos para publicacao manual",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total selecionado: {len(selected_deals)}",
        "",
    ]

    for index, (product, history, score) in enumerate(selected_deals, start=1):
        tweet_text = generate_tweet_text(product, history)
        lines.extend(
            [
                "=" * 72,
                f"POST {index} | score {score} | {product.store}",
                "=" * 72,
                tweet_text,
                "",
                "Dados da oferta:",
                f"- Produto: {product.title}",
                f"- Loja: {product.store}",
                f"- Categoria: {product.category}",
                f"- Preco atual: R$ {product.current_price:.2f}",
                f"- Preco antigo: {product.old_price if product.old_price is not None else 'n/a'}",
                f"- Desconto: {product.discount_percent:.0f}%",
                f"- Link original: {product.url}",
                f"- Link usado no post: {product.affiliate_url or product.url}",
                "",
            ]
        )

    output_path.write_text("\n".join(lines), encoding="utf-8-sig")
    return output_path
