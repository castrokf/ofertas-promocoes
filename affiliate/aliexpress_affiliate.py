from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def generate_aliexpress_affiliate_link(url: str, affiliate_id: str) -> str:
    if not affiliate_id:
        return url
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["aff_fcid"] = affiliate_id
    query["aff_platform"] = "portals-tool"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
