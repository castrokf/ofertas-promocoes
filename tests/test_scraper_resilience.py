import requests

from config import Settings
from main import _scraper_plan
from scrapers.base import HtmlListingScraper


class FakeResponse:
    def __init__(self, status_code: int, url: str = "https://example.com/search") -> None:
        self.status_code = status_code
        self.url = url
        self.text = ""

    def raise_for_status(self) -> None:
        raise requests.HTTPError(f"{self.status_code} error", response=self)


class ProtectedScraper(HtmlListingScraper):
    store_name = "Protected Store"
    base_url = "https://example.com"
    search_url_template = "https://example.com/search?q={query}"


def test_protected_store_stops_after_first_block(monkeypatch):
    scraper = ProtectedScraper(Settings())
    calls = []

    monkeypatch.setattr(scraper, "can_fetch", lambda _url: True)
    monkeypatch.setattr(scraper, "delay", lambda: None)

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse(503, url)

    scraper.session.get = fake_get

    assert scraper.collect_deals(["ssd", "gpu"]) == []
    assert len(calls) == 1


def test_robots_block_stops_store_without_error(monkeypatch):
    scraper = ProtectedScraper(Settings())
    calls = []

    monkeypatch.setattr(scraper, "can_fetch", lambda _url: False)

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return FakeResponse(200, url)

    scraper.session.get = fake_get

    assert scraper.collect_deals(["ssd", "gpu"]) == []
    assert calls == []


def test_disabled_stores_are_removed_from_plan():
    settings = Settings(disabled_stores=("Amazon Brasil", "Nuuvem"))
    stores = [store for store, _categories in _scraper_plan(settings, "all")]

    assert "Amazon Brasil" not in stores
    assert "Nuuvem" not in stores
    assert "Steam" in stores
