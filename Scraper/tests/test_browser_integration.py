"""Opt-in Chromium checks: responses are fulfilled locally, with no live site calls."""

import os
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jumia_reviews import BrowserPageFetcher, collect

pytestmark = pytest.mark.skipif(
    os.getenv("FYP_RUN_BROWSER_TESTS") != "1",
    reason="Set FYP_RUN_BROWSER_TESTS=1 after installing Chromium to run browser integration tests.",
)

PRODUCT = "https://www.jumia.com.ng/test-product-12345.html"
REVIEWS = "https://www.jumia.com.ng/catalog/productratingsreviews/sku/TEST123/"


def html_review(title, day="07-10-2026"):
    return f'<article><div class="stars">4 out of 5</div><h3>{title}</h3><p>Example review.</p><span>{day}</span></article>'


def test_real_chromium_captures_responses_and_follows_review_pagination(monkeypatch):
    pytest.importorskip("playwright.sync_api")
    pages = {
        PRODUCT: '<h1>Example product</h1>' + html_review("First") + f'<a href="{REVIEWS}">All reviews</a>',
        REVIEWS: html_review("First") + html_review("Second") + '<a href="?page=2">Next</a>',
        REVIEWS + "?page=2": html_review("Third", "14-10-2026"),
    }
    def serve_fixture(self, route):
        route.fulfill(status=200, content_type="text/html", body=pages[route.request.url])
    monkeypatch.setattr(BrowserPageFetcher, "_route", serve_fixture)
    monkeypatch.setattr(BrowserPageFetcher, "ensure_allowed", lambda self, url: url)
    fetcher = BrowserPageFetcher("owner@example.test")
    try:
        dataset = collect(PRODUCT, fetcher.get, 5, 50)
        assert dataset["error"] is None
        assert len(dataset["reviews"]) == 3
        assert dataset["duplicates_removed"] == 1
        assert [capture["url"] for capture in fetcher.captures] == list(pages)
        assert all(capture["capture_method"] == "browser_response" for capture in fetcher.captures)
    finally:
        fetcher.close()


def test_real_chromium_http_block_stops_without_exporting_reviews(monkeypatch):
    pytest.importorskip("playwright.sync_api")
    def blocked(self, route):
        route.fulfill(status=403, content_type="text/html", body="<h1>Access denied</h1>")
    monkeypatch.setattr(BrowserPageFetcher, "_route", blocked)
    monkeypatch.setattr(BrowserPageFetcher, "ensure_allowed", lambda self, url: url)
    fetcher = BrowserPageFetcher("owner@example.test")
    try:
        dataset = collect(PRODUCT, fetcher.get, 5, 50)
        assert dataset["status"] == "failed"
        assert "403" in dataset["error"]
        assert dataset["reviews"] == []
        assert fetcher.captures == []
    finally:
        fetcher.close()
