from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.core.config import Settings


class AffiliateService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_url(self, store_slug: str, original_url: str, source: str = "autotechdealsx") -> tuple[str, bool]:
        if store_slug == "amazon" and self.settings.amazon_associate_tag:
            return self._with_query(original_url, {"tag": self.settings.amazon_associate_tag, "utm_source": source}), True
        if store_slug == "mercado-livre" and self.settings.mercado_livre_affiliate_id:
            params = {"matt_word": self.settings.mercado_livre_affiliate_id, "utm_source": source}
            if self.settings.mercado_livre_tool_id:
                params["matt_tool"] = self.settings.mercado_livre_tool_id
            return self._with_query(original_url, params), True
        if store_slug == "aliexpress" and self.settings.aliexpress_affiliate_id:
            return self._with_query(
                original_url,
                {
                    "aff_fcid": self.settings.aliexpress_affiliate_id,
                    "aff_platform": "portals-tool",
                    "utm_source": source,
                },
            ), True
        return self._with_query(original_url, {"utm_source": source}), False

    @staticmethod
    def _with_query(url: str, params: dict[str, str]) -> str:
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query.update({key: value for key, value in params.items() if value})
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
