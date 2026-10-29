"""Offline fixtures exercise collection behaviour without calling Jumia."""

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jumia_reviews import (
    BrowserPageFetcher, CollectionError, FetchedPage, PageFetcher, RobotsPolicy,
    collect, configured_contact, coverage_report, export_dataset, main, parse_date,
    parse_page, product_identity, response_html, save_source_captures,
    select_review_response, validated_url,
)

PRODUCT = "https://www.jumia.com.ng/test-product-12345.html"
REVIEWS = "https://www.jumia.com.ng/catalog/productratingsreviews/?sku=TEST123"


def card(title="Works well", body="Good quality &amp; fast delivery.", day="07-10-2026", rating="4 out of 5", author="Example", native_id=""):
    return f'''<article class="-pvs -hr _bet" {f'data-review-id="{native_id}"' if native_id else ''}>
      <div class="stars _m _al -mvs">{rating}</div><h3>{title}</h3><p>{body}</p>
      <div><span class="-prs">{day}</span><span>by {author}</span></div>
      <div>Verified Purchase</div></article>'''


def test_extracts_text_original_date_rating_and_provenance_without_names():
    result = parse_page("<h1>Test product</h1>" + card(), PRODUCT, PRODUCT)
    assert result.cards_found == 1
    item = result.reviews[0]
    assert item["raw_text"] == "Works well\nGood quality & fast delivery."
    assert item["reviewed_at"] == "2026-10-07"
    assert item["star_rating"] == 4
    assert item["product_url"] == PRODUCT
    assert item["external_product_id"] == "12345"
    assert item["subject_type"] == "product"
    assert item["verified_purchase"] is True
    assert item["review_id_kind"] == "content_fingerprint"
    assert "Example" not in json.dumps(item)
    assert "sentiment" not in item


@pytest.mark.parametrize("value,expected", [("03-04-2026", "2026-04-03"), ("2026-04-03", "2026-04-03"), ("31-02-2026", None), ("yesterday", None), ("", None)])
def test_dates_are_not_fabricated(value, expected):
    assert parse_date(value) == expected


def test_malformed_reviews_are_retained_but_excluded_from_import():
    result = parse_page(card(day="") + card(rating="6 out of 5") + card(title="", body=""), PRODUCT, PRODUCT)
    assert result.reviews == []
    assert len(result.excluded) == 3
    assert "original review date" in result.excluded[0]["exclusion_reasons"][0]


def test_date_in_review_prose_is_not_used_as_publication_date():
    page = parse_page(card(body="Ordered <span>01-01-2026</span> and waited.", day=""), PRODUCT, PRODUCT)
    assert page.reviews == []
    assert page.excluded[0]["reviewed_at"] is None


def test_nested_articles_and_product_recommendations_are_not_counted():
    html = "<article><h3>Customer feedback</h3>" + card() + "</article>"
    html += '<article class="prd"><div class="stars">5 out of 5</div><h3>Recommended product</h3></article>'
    assert len(parse_page(html, PRODUCT, PRODUCT).reviews) == 1


def test_native_ids_and_different_authors_distinguish_identical_reviews():
    page = parse_page(card(native_id="review-1") + card(author="Other"), PRODUCT, PRODUCT)
    assert page.reviews[0]["source_review_id"] == "review-1"
    assert page.reviews[0]["source_review_id"] != page.reviews[1]["source_review_id"]


def test_sku_path_review_urls_keep_actual_product_identifier():
    url = "https://www.jumia.com.ng/catalog/productratingsreviews/sku/IT724GP6OJ3RRNAFAMZ/?page=2"
    assert product_identity(url) == "IT724GP6OJ3RRNAFAMZ"


def test_collection_follows_links_deduplicates_and_reports_weekly_coverage():
    pages = {
        PRODUCT: card() + '<a href="/catalog/productratingsreviews/?sku=TEST123">See all</a>',
        REVIEWS: card() + card(title="Poor battery", rating="1 out of 5", day="14-10-2026") + '<a href="?sku=TEST123&amp;page=2">Next</a>',
        REVIEWS + "&page=2": card(title="Okay", day="15-10-2026", rating="3 out of 5"),
    }
    data = collect(PRODUCT, pages.__getitem__, 5, 50)
    assert data["status"] == "complete"
    assert len(data["reviews"]) == 3
    assert data["duplicates_removed"] == 1
    assert data["pages_visited"] == list(pages)
    assert coverage_report(data)["reviews_by_week"] == {"2026-10-05": 1, "2026-10-12": 2}


def test_partial_failure_preserves_previous_results():
    def fetch(url):
        if url == PRODUCT:
            return card() + f'<a href="{REVIEWS}">See all</a>'
        raise CollectionError("HTTP 403")
    result = collect(PRODUCT, fetch, 5, 50)
    assert result["status"] == "partial"
    assert result["error"] == "HTTP 403"
    assert len(result["reviews"]) == 1


def test_page_and_review_limits_are_reported():
    html = card() + card(title="Different") + f'<a href="{REVIEWS}">All</a>'
    data = collect(PRODUCT, lambda url: html, 5, 1)
    assert len(data["reviews"]) == 1
    assert data["limit_reached"] is True
    data = collect(PRODUCT, lambda url: html, 1, 50)
    assert len(data["pages_visited"]) == 1
    assert data["limit_reached"] is True


def test_unknown_layout_and_access_challenge_are_errors_not_empty_success():
    result = collect(PRODUCT, lambda url: "<h1>Unexpected layout</h1>", 2, 50)
    assert result["status"] == "failed"
    with pytest.raises(CollectionError, match="challenge"):
        parse_page("<title>Just a moment...</title>", PRODUCT, PRODUCT)


def test_explicit_zero_reviews_is_distinguished_from_layout_change():
    result = collect(PRODUCT, lambda url: "<h2>Product Reviews (0)</h2>", 2, 50)
    assert result["status"] == "complete"
    assert result["error"] is None
    assert result["reviews"] == []


def test_exports_backend_compatible_batches_and_keeps_original_provenance(tmp_path):
    data = collect(PRODUCT, lambda url: card(), 1, 50)
    data["reviews"] = [dict(data["reviews"][0], source_review_id=str(i)) for i in range(1001)]
    output = tmp_path / "export"
    report = export_dataset(data, output, business_id=7)
    first = json.loads((output / "import-001.json").read_text())["reviews"]
    second = json.loads((output / "import-002.json").read_text())["reviews"]
    assert len(first) == 1000 and len(second) == 1
    assert set(first[0]) == {"business_id", "raw_text", "source", "star_rating", "reviewed_at", "source_review_id"}
    assert first[0]["source_review_id"] == "0"
    assert first[0]["business_id"] == 7
    assert report["import_files"] == ["import-001.json", "import-002.json"]
    raw = json.loads((output / "reviews.raw.json").read_text())
    assert raw["reviews"][0]["product_url"] == PRODUCT
    with pytest.raises(FileExistsError):
        export_dataset(data, output)


def test_robots_longest_allow_rule_and_wildcard_query_blocks():
    policy = RobotsPolicy("User-agent: *\nDisallow: /catalog/\nAllow: /catalog/productratingsreviews/\nDisallow: /*sort=\nDisallow: /private/*$\nCrawl-delay: 4")
    assert policy.allows(REVIEWS)
    assert not policy.allows("https://www.jumia.com.ng/catalog/phones/")
    assert not policy.allows(PRODUCT + "?sort=rating")
    assert not policy.allows("https://www.jumia.com.ng/private/test")
    assert policy.delay == 4
    assert policy.allows(PRODUCT)


def test_most_specific_bot_group_is_used_without_inheriting_wildcard():
    policy = RobotsPolicy("User-agent: *\nDisallow: /\nUser-agent: FYPReviewCollector\nAllow: /")
    assert policy.allows(PRODUCT)


@pytest.mark.parametrize("url", ["http://www.jumia.com.ng/a", "https://jumia.com.ng.evil.example/a", "https://www.jumia.co.ke/a", "https://user@www.jumia.com.ng/a"])
def test_only_expected_nigerian_public_host_is_accepted(url):
    with pytest.raises(CollectionError):
        validated_url(url)


def test_fetcher_stops_at_rate_limit_without_requesting_more_pages(monkeypatch):
    fetcher = PageFetcher("owner@example.test")
    calls = []
    def handle(request):
        calls.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /", headers={"content-type": "text/plain"})
        return httpx.Response(429)
    fetcher.client.close()
    fetcher.client = httpx.Client(transport=httpx.MockTransport(handle))
    monkeypatch.setattr("jumia_reviews.time.sleep", lambda seconds: None)
    try:
        with pytest.raises(CollectionError, match="429"):
            fetcher.get(PRODUCT)
        assert len(calls) == 2
    finally:
        fetcher.close()


def test_redirect_outside_jumia_is_rejected(monkeypatch):
    fetcher = PageFetcher("owner@example.test")
    def handle(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(302, headers={"location": "https://example.test/"})
    fetcher.client.close()
    fetcher.client = httpx.Client(transport=httpx.MockTransport(handle))
    monkeypatch.setattr("jumia_reviews.time.sleep", lambda seconds: None)
    try:
        with pytest.raises(CollectionError, match="Jumia|jumia"):
            fetcher.get(PRODUCT)
    finally:
        fetcher.close()


def test_gone_listing_reports_actionable_saved_page_fallback(monkeypatch):
    fetcher = PageFetcher("owner@example.test")
    def handle(request):
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(410)
    fetcher.client.close()
    fetcher.client = httpx.Client(transport=httpx.MockTransport(handle))
    monkeypatch.setattr("jumia_reviews.time.sleep", lambda seconds: None)
    try:
        with pytest.raises(CollectionError, match="410.*--html"):
            fetcher.get(PRODUCT)
    finally:
        fetcher.close()


def test_saved_html_cli_creates_import_without_network(tmp_path):
    fixture = tmp_path / "page.html"
    fixture.write_text(card(), encoding="utf-8")
    output = tmp_path / "collected"
    assert main(["--url", PRODUCT, "--html", str(fixture), "--output", str(output)]) == 0
    payload = json.loads((output / "import-001.json").read_text())
    assert payload["reviews"][0]["reviewed_at"] == "2026-10-07"
    assert "business_id" not in payload["reviews"][0]


def test_missing_live_contact_is_rejected_before_fetch_or_export(tmp_path):
    output = tmp_path / "collected"
    assert main(["--url", PRODUCT, "--contact", "", "--output", str(output)]) == 1
    assert not output.exists()


def response(url, html, resource_type="document", content_type="text/html", status=200):
    return {"url": url, "body": html, "resource_type": resource_type,
            "content_type": content_type, "status": status}


def test_review_response_is_preferred_over_product_preview_and_assets():
    selected = select_review_response([
        response(PRODUCT, card()),
        response(PRODUCT, card() + card(title="Unrelated asset"), "script"),
        response(REVIEWS, card() + card(title="Second review"), "xhr"),
        response("https://example.test/reviews", card() * 10),
    ], PRODUCT)
    assert selected["url"] == REVIEWS
    assert selected["cards_found"] == 2


def test_review_html_inside_json_response_is_detected():
    envelope = json.dumps({"data": {"html": card()}})
    selected = select_review_response([response(REVIEWS, envelope, "fetch", "application/json")], PRODUCT)
    assert selected["cards_found"] == 1
    assert "<article" in selected["html"]
    assert response_html('{"reviews":[]}', "application/json") == []
    assert response_html('bad JSON', "application/json") == []


def test_other_product_review_responses_are_not_selected():
    preview = card() + f'<a href="{REVIEWS}">All reviews</a>'
    unrelated = "https://www.jumia.com.ng/catalog/productratingsreviews/?sku=OTHER"
    selected = select_review_response([
        response(PRODUCT, preview),
        response(unrelated, card() * 10, "xhr"),
        response(REVIEWS, card(), "fetch"),
    ], PRODUCT)
    assert selected["url"] == REVIEWS


def test_generic_feedback_heading_is_not_used_as_product_name():
    parsed = parse_page('<h1>Verified Customer Feedback</h1>' + card(), REVIEWS, PRODUCT)
    assert parsed.product_name is None


def test_failed_or_unrelated_responses_do_not_become_a_dataset():
    assert select_review_response([
        response(REVIEWS, card(), status=403),
        response(PRODUCT, "<html><body>No reviews here</body></html>"),
        response(PRODUCT + "/api", card(), "xhr"),
    ], PRODUCT) is None


def test_response_source_url_is_used_instead_of_initial_navigation_url():
    data = collect(PRODUCT, lambda url: FetchedPage(card(), REVIEWS), 1, 50)
    assert data["reviews"][0]["source_url"] == REVIEWS
    assert data["reviews"][0]["product_url"] == PRODUCT
    assert data["pages_visited"] == [REVIEWS]


def test_browser_fetcher_selects_response_body_without_dom_scraping(monkeypatch):
    fetcher = BrowserPageFetcher("owner@example.test")
    captured = SimpleNamespace(
        url=REVIEWS, status=200, headers={"content-type": "text/html"},
        request=SimpleNamespace(resource_type="xhr"), text=lambda: card(),
    )
    def navigate(url, **kwargs):
        fetcher.responses.append(captured)
        return SimpleNamespace(status=200)
    locator = SimpleNamespace(first=SimpleNamespace(wait_for=lambda **kwargs: None))
    fetcher.page = SimpleNamespace(goto=navigate, locator=lambda selector: locator)
    monkeypatch.setattr(fetcher, "ensure_allowed", lambda url: url)
    try:
        result = fetcher.get(PRODUCT)
        assert result.url == REVIEWS
        assert result.html == card()
        assert fetcher.captures[0]["capture_method"] == "browser_response"
        assert fetcher.captures[0]["requested_url"] == PRODUCT
    finally:
        fetcher.close()


def test_browser_http_block_is_not_hidden_by_other_successful_responses(monkeypatch):
    fetcher = BrowserPageFetcher("owner@example.test")
    fetcher.page = SimpleNamespace(goto=lambda *args, **kwargs: SimpleNamespace(status=410))
    monkeypatch.setattr(fetcher, "ensure_allowed", lambda url: url)
    try:
        with pytest.raises(CollectionError, match="410"):
            fetcher.get(PRODUCT)
        assert fetcher.captures == []
    finally:
        fetcher.close()


def test_url_prompt_works_with_existing_saved_html_mode(tmp_path, monkeypatch):
    fixture = tmp_path / "page.html"
    fixture.write_text(card())
    prompts = []
    def answer(prompt):
        prompts.append(prompt)
        return PRODUCT
    monkeypatch.setattr("builtins.input", answer)
    output = tmp_path / "prompted"
    assert main(["--html", str(fixture), "--output", str(output)]) == 0
    assert len(prompts) == 1 and "URL" in prompts[0]
    assert len(json.loads((output / "import-001.json").read_text())["reviews"]) == 1


def test_local_contact_config_does_not_execute_shell_values(tmp_path, monkeypatch):
    monkeypatch.delenv("JUMIA_SCRAPER_CONTACT", raising=False)
    monkeypatch.setattr("jumia_reviews.SCRAPER_ROOT", tmp_path)
    (tmp_path / ".env").write_text('JUMIA_SCRAPER_CONTACT="owner@example.test"\nOTHER=ignored\n')
    assert configured_contact() == "owner@example.test"
    monkeypatch.setenv("JUMIA_SCRAPER_CONTACT", "override@example.test")
    assert configured_contact() == "override@example.test"


def test_selected_response_html_is_saved_with_source_manifest(tmp_path):
    save_source_captures([{"url": REVIEWS, "html": card(), "capture_method": "browser_response"}], tmp_path)
    manifest = json.loads((tmp_path / "sources/manifest.json").read_text())
    assert manifest["pages"][0]["url"] == REVIEWS
    assert "html" not in manifest["pages"][0]
    assert (tmp_path / "sources/page-001.html").read_text() == card()


def test_saved_collection_can_use_more_than_one_hundred_review_pages(tmp_path):
    fixture = tmp_path / "page.html"
    fixture.write_text(card())
    output = tmp_path / "long-collection"
    assert main(["--url", PRODUCT, "--html", str(fixture), "--max-pages", "156", "--output", str(output)]) == 0
    assert json.loads((output / "report.json").read_text())["limit_reached"] is False
    assert main(["--url", PRODUCT, "--html", str(fixture), "--max-pages", "501", "--output", str(tmp_path / "invalid")]) == 1
