from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def generate_amazon_affiliate_link(url: str, associate_tag: str) -> str:
    if not associate_tag:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["tag"] = associate_tag
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
