from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from affiliate.aliexpress_affiliate import generate_aliexpress_affiliate_link
from affiliate.amazon_affiliate import generate_amazon_affiliate_link
from config import Settings
from database.models import ProductDeal


def _generate_mercadolivre_affiliate_link(
    url: str,
    affiliate_id: str,
    tool_id: str = "",
) -> str:
    if not affiliate_id:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["matt_word"] = affiliate_id
    if tool_id:
        query["matt_tool"] = tool_id
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def generate_affiliate_link(product: ProductDeal, settings: Settings) -> str:
    if product.store == "Amazon Brasil":
        return generate_amazon_affiliate_link(product.url, settings.amazon_associate_tag)
    if product.store == "AliExpress":
        return generate_aliexpress_affiliate_link(product.url, settings.aliexpress_affiliate_id)
    if product.store == "Mercado Livre":
        return _generate_mercadolivre_affiliate_link(
            product.url,
            settings.mercadolivre_affiliate_id,
            settings.mercadolivre_tool_id,
        )
    return product.url
