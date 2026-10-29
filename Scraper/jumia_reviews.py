"""Collect public Jumia Nigeria product reviews without inventing dates or labels."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import httpx

BOT_NAME = "FYPReviewCollector"
HOSTS = {"jumia.com.ng", "www.jumia.com.ng"}
MIN_DELAY = 3.0
BATCH_SIZE = 1000  # Laravel's review batch limit, not the NLP service's chunk size.
SCRAPER_ROOT = Path(__file__).resolve().parent
COLLECTIONS_ROOT = SCRAPER_ROOT / "data" / "collections"


class CollectionError(Exception):
    """An actionable collection error, including a blocked or changed page."""


@dataclass
class FetchedPage:
    html: str
    url: str


def response_html(body: str, content_type: str) -> list[str]:
    """Find HTML fragments in a response, including JSON HTML envelopes."""
    if "html" in content_type.lower():
        return [body]
    if "json" not in content_type.lower():
        return []
    try:
        payload = json.loads(body)
    except ValueError:
        return []
    fragments = []

    def visit(value):
        if isinstance(value, str) and re.search(r"<(?:article|html|div|section)\b", value, re.I):
            fragments.append(value)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return fragments


def select_review_response(responses: list[dict], product_url: str) -> dict | None:
    """Prefer a full review response over a product-page preview or unrelated data."""
    expected_skus = set()
    if "/catalog/productratingsreviews/" in urlsplit(product_url).path:
        expected_skus.add(product_identity(product_url))
    else:
        for response in responses:
            if response["status"] != 200 or response.get("resource_type") != "document":
                continue
            if urlsplit(response["url"]).path != urlsplit(product_url).path:
                continue
            for html in response_html(response["body"], response["content_type"]):
                link = parse_page(html, response["url"], product_url).review_url
                if link:
                    expected_skus.add(product_identity(link))
    candidates = []
    for response in responses:
        if response["status"] != 200:
            continue
        try:
            url = validated_url(response["url"])
        except (CollectionError, ValueError):
            continue
        is_review_url = "/catalog/productratingsreviews/" in urlsplit(url).path
        if is_review_url and expected_skus and product_identity(url) not in expected_skus:
            continue
        if response.get("resource_type") != "document" and not is_review_url:
            continue
        for html in response_html(response["body"], response["content_type"]):
            page = parse_page(html, url, product_url)
            if page.cards_found or page.review_url or page.explicitly_empty:
                candidates.append((
                    (bool(is_review_url and page.cards_found), bool(page.cards_found), page.cards_found),
                    {**response, "html": html, "cards_found": page.cards_found},
                ))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


def validated_url(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme != "https" or parts.hostname not in HOSTS
        or parts.username or parts.password or parts.port not in (None, 443)
    ):
        raise CollectionError("Use an HTTPS product/review URL on www.jumia.com.ng.")
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def normalise_text(value: str) -> str:
    return " ".join(value.split())


def parse_date(value: str) -> str | None:
    """Jumia's numeric dates are day-month-year; never substitute scrape time."""
    match = re.search(r"\b(\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2})\b", value)
    if not match:
        return None
    token = match.group(1)
    try:
        parsed = datetime.strptime(token, "%Y-%m-%d" if token[4] == "-" else "%d-%m-%Y")
        return parsed.date().isoformat()
    except ValueError:
        return None


def product_identity(url: str) -> str:
    parts = urlsplit(url)
    sku = parse_qs(parts.query).get("sku", [None])[0]
    if sku:
        return sku
    sku_path = re.search(r"/productratingsreviews/sku/([^/]+)/?", parts.path)
    if sku_path:
        return sku_path.group(1)
    match = re.search(r"-(\d+)\.html$", parts.path)
    return match.group(1) if match else parts.path.rstrip("/")


@dataclass
class ParsedPage:
    reviews: list[dict] = field(default_factory=list)
    excluded: list[dict] = field(default_factory=list)
    review_url: str | None = None
    next_url: str | None = None
    product_name: str | None = None
    cards_found: int = 0
    explicitly_empty: bool = False


def parse_page(html: str, page_url: str, product_url: str) -> ParsedPage:
    soup = BeautifulSoup(html, "html.parser")
    page_title = normalise_text(soup.title.get_text(" ", strip=True)) if soup.title else ""
    if re.search(r"access denied|verify you are human|just a moment|captcha", page_title, re.I):
        raise CollectionError("Jumia returned an access challenge; collection stopped.")

    heading = soup.select_one("h1")
    product_name = heading.get_text(" ", strip=True) if heading else None
    if product_name and normalise_text(product_name).lower() == "verified customer feedback":
        product_name = None
    page = ParsedPage(product_name=product_name)
    for link in soup.select("a[href]"):
        href = urljoin(page_url, link["href"])
        if "/catalog/productratingsreviews/" in urlsplit(href).path:
            page.review_url = validated_url(href)
            break

    # Each public review is an article with a rating and a title/body. Avoid
    # product listing articles and the page's aggregate rating widget.
    for card in soup.select("article"):
        if "prd" in card.get("class", []):
            continue
        owned = lambda selector: [node for node in card.select(selector) if node.find_parent("article") is card]
        rating_nodes = owned(".stars, [itemprop='ratingValue']")
        title_nodes = owned("h3, [itemprop='name']")
        rating_node = rating_nodes[0] if rating_nodes else None
        title_node = title_nodes[0] if title_nodes else None
        body_nodes = owned("p")
        if rating_node is None or (title_node is None and not body_nodes):
            continue
        page.cards_found += 1
        rating_raw = rating_node.get("content") or rating_node.get_text(" ", strip=True)
        rating_match = re.fullmatch(r"\s*([1-5])(?:\s+(?:out of|/)\s*5)?\s*", rating_raw, re.I)
        rating = int(rating_match.group(1)) if rating_match else None
        title = normalise_text(title_node.get_text(" ", strip=True)) if title_node else ""
        body = "\n".join(filter(None, (normalise_text(node.get_text(" ", strip=True)) for node in body_nodes)))
        raw_text = "\n".join(dict.fromkeys(filter(None, (title, body))))
        date_nodes = owned("time, [itemprop='datePublished']")
        date_node = date_nodes[0] if date_nodes else None
        date_raw = (
            date_node.get("datetime") or date_node.get("content") or date_node.get_text(" ", strip=True)
        ) if date_node else ""
        if not date_raw:
            # Do not let a date mentioned inside review prose become its date.
            candidates = [node.get_text(" ", strip=True) for node in owned("span") if not node.find_parent("p")]
            date_raw = next((text for text in candidates if re.fullmatch(r"\d{2}-\d{2}-\d{4}", text)), "")
        reviewed_at = parse_date(date_raw)
        reasons = []
        if not raw_text:
            reasons.append("missing review text")
        if rating is None:
            reasons.append("missing or invalid star rating")
        if reviewed_at is None:
            reasons.append("missing or invalid original review date")
        record = {
            "raw_text": raw_text, "title": title, "body": body,
            "star_rating": rating, "reviewed_at": reviewed_at,
            "reviewed_at_raw": date_raw, "rating_raw": rating_raw,
            "source": "jumia_product_review", "source_url": page_url,
            "product_url": product_url, "external_product_id": product_identity(product_url),
            "subject_type": "product",
            "verified_purchase": bool(re.search(r"Verified Purchase", card.get_text(" "), re.I)),
        }
        # A name is used only to distinguish otherwise identical reviews when
        # the page exposes no ID. Reviewer names are not exported.
        author_node = next((node for node in owned("span") if re.match(r"^by\s+", node.get_text(strip=True), re.I)), None)
        author = normalise_text(author_node.get_text(" ", strip=True)) if author_node else ""
        native_id = card.get("data-review-id") or card.get("id")
        fingerprint = json.dumps([product_identity(product_url), reviewed_at, rating, title, body, author], ensure_ascii=False)
        record["source_review_id"] = str(native_id) if native_id else hashlib.sha256(fingerprint.encode()).hexdigest()
        record["review_id_kind"] = "native" if native_id else "content_fingerprint"
        if reasons:
            record["exclusion_reasons"] = reasons
            page.excluded.append(record)
        else:
            page.reviews.append(record)

    current = urlsplit(page_url)
    current_query = parse_qs(current.query)
    try:
        current_number = int(current_query.get("page", ["1"])[0])
    except ValueError:
        raise CollectionError("Review page has an invalid page number.") from None
    for link in soup.select("a[href]"):
        candidate = urljoin(page_url, link["href"])
        parts = urlsplit(candidate)
        query = parse_qs(parts.query)
        if (
            parts.path == current.path
            and query.get("sku") == current_query.get("sku")
            and query.get("page") == [str(current_number + 1)]
        ):
            page.next_url = validated_url(candidate)
            break
    page.explicitly_empty = bool(re.search(
        r"(?:product reviews|comments from verified purchases)\s*\(\s*0\s*\)|no (?:customer |product )?reviews (?:yet|available)",
        soup.get_text(" ", strip=True), re.I,
    ))
    return page


class RobotsPolicy:
    """Match wildcard/terminal-$ rules by longest path; Allow wins a tie."""

    def __init__(self, text: str):
        groups: list[tuple[list[str], list[tuple[str, str]]]] = []
        agents: list[str] = []
        rules: list[tuple[str, str]] = []
        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if rules:
                    groups.append((agents, rules))
                    agents, rules = [], []
                agents.append(value.lower())
            elif agents and key in {"allow", "disallow", "crawl-delay"}:
                rules.append((key, value))
        if agents:
            groups.append((agents, rules))
        matches = []
        for group_agents, group_rules in groups:
            scores = [len(agent) if agent != "*" else 0 for agent in group_agents if agent == "*" or agent in BOT_NAME.lower()]
            if scores:
                matches.append((max(scores), group_rules))
        best = max((score for score, _ in matches), default=-1)
        self.rules = [rule for score, group in matches if score == best for rule in group]
        self.delay = MIN_DELAY
        for key, value in self.rules:
            if key == "crawl-delay":
                try:
                    self.delay = max(self.delay, float(value))
                except ValueError:
                    pass

    def allows(self, url: str) -> bool:
        parts = urlsplit(url)
        target = parts.path + ("?" + parts.query if parts.query else "")
        matches = []
        for kind, pattern in self.rules:
            if kind not in {"allow", "disallow"} or not pattern:
                continue
            terminal = pattern.endswith("$")
            expression = "^" + ".*".join(re.escape(part) for part in pattern.removesuffix("$").split("*"))
            if re.search(expression + ("$" if terminal else ""), target):
                matches.append((len(pattern.replace("*", "").removesuffix("$")), kind == "allow"))
        return max(matches, default=(0, True))[1]


class PageFetcher:
    def __init__(self, contact: str, delay: float = MIN_DELAY):
        if not contact or not re.fullmatch(r"(?:https?://[^\s()]+|[^\s@()]+@[^\s@()]+\.[^\s@()]+)", contact):
            raise CollectionError("Live collection needs --contact EMAIL_OR_URL (or JUMIA_SCRAPER_CONTACT).")
        if not MIN_DELAY <= delay <= 300:
            raise CollectionError("--delay must be between 3 and 300 seconds.")
        self.delay = delay
        self.contact = contact
        self.last_request: float | None = None
        self.policies: dict[str, RobotsPolicy] = {}
        self.captures: list[dict] = []
        self.client = httpx.Client(
            headers={"User-Agent": f"{BOT_NAME}/1.0 (+{contact})", "Accept": "text/html, text/plain;q=0.9"},
            timeout=30, follow_redirects=False,
        )

    def close(self) -> None:
        self.client.close()

    def _request(self, url: str) -> httpx.Response:
        if self.last_request is not None:
            time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        try:
            response = self.client.get(url)
        except httpx.HTTPError as exc:
            raise CollectionError(f"Request failed for {url}: {exc}") from exc
        if response.status_code in {401, 403, 429}:
            raise CollectionError(f"Jumia returned HTTP {response.status_code}; stopped without retrying or bypassing access controls.")
        return response

    def ensure_allowed(self, url: str) -> str:
        url = validated_url(url)
        origin = f"https://{urlsplit(url).netloc}"
        if origin not in self.policies:
            response = self._request(origin + "/robots.txt")
            if response.status_code == 404:
                policy = RobotsPolicy("")
            elif response.status_code == 200 and "<html" not in response.text.lower():
                policy = RobotsPolicy(response.text)
            else:
                raise CollectionError("Could not read robots.txt reliably; no review pages were requested.")
            self.policies[origin] = policy
            self.delay = max(self.delay, policy.delay)
        if not self.policies[origin].allows(url):
            raise CollectionError(f"robots.txt disallows this URL: {url}")
        return url

    def get(self, url: str) -> str:
        url = validated_url(url)
        for _ in range(6):
            url = self.ensure_allowed(url)
            response = self._request(url)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise CollectionError("Redirect is missing its destination.")
                url = validated_url(urljoin(url, location))
                continue
            if response.status_code == 410:
                raise CollectionError(
                    f"Jumia returned HTTP 410 (Gone) for {url}. Try a current product/review URL, "
                    "or use --html with a review page saved from your browser."
                )
            if response.status_code != 200:
                raise CollectionError(f"HTTP {response.status_code} for {url}")
            if "html" not in response.headers.get("content-type", "").lower():
                raise CollectionError("Expected an HTML product/review page.")
            self.captures.append({"url": url, "html": response.text, "capture_method": "http_response", "status": 200})
            return response.text
        raise CollectionError("Too many redirects.")


class BrowserPageFetcher(PageFetcher):
    """Observe real browser responses and keep only the one containing reviews."""

    def __init__(self, contact: str, delay: float = MIN_DELAY, headed: bool = False):
        super().__init__(contact, delay)
        self.headed = headed
        self.runtime = self.browser = self.context = self.page = None
        self.responses = []
        self.navigation_error = None

    def _start(self) -> None:
        if self.page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise CollectionError(
                "Browser mode needs Playwright. Run .venv/bin/python -m pip install -r "
                "Scraper/requirements.txt, then .venv/bin/python -m playwright install chromium."
            ) from exc
        self.runtime = sync_playwright().start()
        self.browser = self.runtime.chromium.launch(headless=not self.headed)
        bootstrap = self.browser.new_page()
        actual_agent = bootstrap.evaluate("navigator.userAgent")
        bootstrap.close()
        self.context = self.browser.new_context(
            user_agent=f"{actual_agent} {BOT_NAME}/1.0 (+{self.contact})",
            service_workers="block",
        )
        self.page = self.context.new_page()
        self.page.route("**/*", self._route)
        self.page.on("response", lambda response: self.responses.append(response))

    def _route(self, route) -> None:
        request = route.request
        # Only document/review traffic is needed. Avoid ads, trackers, images,
        # fonts and unrelated APIs; keep same-origin scripts/styles available.
        is_content = request.resource_type == "document" or (
            request.resource_type in {"xhr", "fetch"}
            and "/catalog/productratingsreviews/" in urlsplit(request.url).path
        )
        if not is_content:
            if request.resource_type in {"script", "stylesheet"} and urlsplit(request.url).hostname in HOSTS:
                route.continue_()
            else:
                route.abort()
            return
        try:
            self.ensure_allowed(request.url)
            if self.last_request is not None:
                time.sleep(max(0, self.delay - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            route.continue_()
        except (CollectionError, ValueError) as exc:
            self.navigation_error = str(exc)
            route.abort()

    def get(self, url: str) -> FetchedPage:
        url = self.ensure_allowed(url)
        try:
            self._start()
            self.responses.clear()
            self.navigation_error = None
            document = self.page.goto(url, wait_until="load", timeout=30000)
            if self.navigation_error:
                raise CollectionError(self.navigation_error)
            if document is not None and document.status in {401, 403, 410, 429}:
                raise CollectionError(f"Browser request returned HTTP {document.status} for {url}; collection stopped.")
            # A late review fragment can arrive after the document. Waiting for
            # review markup allows its response to finish without relying on ads.
            try:
                self.page.locator("article h3").first.wait_for(state="attached", timeout=5000)
            except Exception:
                pass
            payloads = []
            for response in self.responses:
                kind = response.request.resource_type
                if kind != "document" and not (
                    kind in {"xhr", "fetch"} and "/catalog/productratingsreviews/" in urlsplit(response.url).path
                ):
                    continue
                if response.status in {401, 403, 410, 429}:
                    raise CollectionError(f"Review response returned HTTP {response.status}; collection stopped.")
                content_type = response.headers.get("content-type", "")
                if response.status != 200 or not any(token in content_type for token in ("html", "json")):
                    continue
                payloads.append({"url": response.url, "status": response.status, "content_type": content_type,
                                 "resource_type": kind, "body": response.text()})
            selected = select_review_response(payloads, url)
            if selected is None:
                raise CollectionError("No browser response contained recognised review HTML or a full-review link.")
            self.captures.append({
                "url": selected["url"], "requested_url": url, "html": selected["html"],
                "capture_method": "browser_response", "status": selected["status"],
                "resource_type": selected["resource_type"], "cards_found": selected["cards_found"],
            })
            return FetchedPage(selected["html"], selected["url"])
        except CollectionError:
            raise
        except Exception as exc:
            raise CollectionError(f"Browser collection failed: {exc}") from exc

    def close(self) -> None:
        try:
            if self.browser:
                self.browser.close()
        finally:
            try:
                if self.runtime:
                    self.runtime.stop()
            finally:
                super().close()


def collect(url: str, fetch, max_pages: int, max_reviews: int) -> dict:
    """Collect one product, following the actual review/pagination links only."""
    collected_at = datetime.now(timezone.utc).isoformat()
    records, excluded, visited = [], [], []
    seen_ids: set[tuple[str, str]] = set()
    duplicates = 0
    product_name = None
    next_url = url
    error = None
    truncated = False
    for _ in range(max_pages):
        if not next_url or next_url in visited:
            break
        current_url = next_url
        try:
            fetched = fetch(current_url)
            if isinstance(fetched, FetchedPage):
                current_url = validated_url(fetched.url)
                html = fetched.html
            else:
                html = fetched
            page = parse_page(html, current_url, url)
            visited.append(current_url)
            product_name = product_name or page.product_name
            if not page.cards_found and not page.review_url and not page.explicitly_empty:
                raise CollectionError("No recognised review cards or review link: the page may be blocked or its layout has changed.")
            excluded.extend(page.excluded)
            for record in page.reviews:
                key = (record["external_product_id"], record["source_review_id"])
                if key in seen_ids:
                    duplicates += 1
                    continue
                seen_ids.add(key)
                record["collected_at"] = collected_at
                if len(records) < max_reviews:
                    records.append(record)
                else:
                    truncated = True
            # A product detail page may show a preview of reviews; the full
            # review page is the next request, not a guessed endpoint.
            next_url = page.review_url if page.review_url and "/catalog/productratingsreviews/" not in urlsplit(current_url).path else page.next_url
            if len(records) >= max_reviews:
                truncated = truncated or bool(next_url)
                break
        except (CollectionError, OSError) as exc:
            error = str(exc)
            break
    else:
        truncated = bool(next_url)
    return {
        "schema_version": 1, "collected_at": collected_at,
        "product_url": url, "product_name": product_name,
        "subject_type": "product", "seller_attribution": "not_established",
        "status": "partial" if error and records else "failed" if error else "complete",
        "error": error, "limit_reached": truncated,
        "pages_visited": visited, "duplicates_removed": duplicates,
        "reviews": records, "excluded_reviews": excluded,
    }


def coverage_report(dataset: dict) -> dict:
    counts = Counter()
    ratings = Counter()
    for review in dataset["reviews"]:
        day = date.fromisoformat(review["reviewed_at"])
        counts[(day - timedelta(days=day.weekday())).isoformat()] += 1
        ratings[str(review["star_rating"])] += 1
    dates = sorted(review["reviewed_at"] for review in dataset["reviews"])
    return {
        "review_count": len(dates), "excluded_count": len(dataset["excluded_reviews"]),
        "earliest_review": dates[0] if dates else None,
        "latest_review": dates[-1] if dates else None,
        "observed_weeks": len(counts), "reviews_by_week": dict(sorted(counts.items())),
        "star_rating_counts": dict(sorted(ratings.items())),
        "note": "Weekly coverage is descriptive, not evidence of forecast accuracy or sales performance.",
    }


def export_dataset(dataset: dict, output: Path, business_id: int | None = None) -> dict:
    """A new directory prevents accidental overwrite; raw provenance is retained."""
    output.mkdir(parents=True, exist_ok=False)
    dataset["coverage"] = coverage_report(dataset)
    (output / "reviews.raw.json").write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    batches = []
    for start in range(0, len(dataset["reviews"]), BATCH_SIZE):
        reviews = []
        for record in dataset["reviews"][start:start + BATCH_SIZE]:
            item = {key: record[key] for key in ("raw_text", "source", "star_rating", "reviewed_at", "source_review_id") if key in record}
            if business_id is not None:
                item["business_id"] = business_id
            reviews.append(item)
        filename = f"import-{len(batches) + 1:03d}.json"
        (output / filename).write_text(json.dumps({"reviews": reviews}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        batches.append(filename)
    report = {key: value for key, value in dataset.items() if key not in {"reviews", "excluded_reviews"}}
    report["import_files"] = batches
    report["import_business_id"] = business_id
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def configured_contact() -> str | None:
    if os.getenv("JUMIA_SCRAPER_CONTACT"):
        return os.environ["JUMIA_SCRAPER_CONTACT"]
    local_config = SCRAPER_ROOT / ".env"
    if local_config.is_file():
        for line in local_config.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == "JUMIA_SCRAPER_CONTACT":
                return value.strip().strip("\"'") or None
    return None


def save_source_captures(captures: list[dict], output: Path) -> None:
    if not captures:
        return
    sources = output / "sources"
    sources.mkdir()
    manifest = []
    for index, capture in enumerate(captures, start=1):
        filename = f"page-{index:03d}.html"
        (sources / filename).write_text(capture["html"], encoding="utf-8")
        manifest.append({key: value for key, value in capture.items() if key != "html"} | {"file": filename})
    (sources / "manifest.json").write_text(json.dumps({"pages": manifest}, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", help="Jumia product/full-review URL; prompts when omitted")
    parser.add_argument("--contact", default=configured_contact(), help="Bot owner's contact email or URL; also read from Scraper/.env")
    parser.add_argument("--transport", choices=("browser", "http"), default="browser", help="Browser response capture (default), or direct HTTP")
    parser.add_argument("--headed", action="store_true", help="Show the browser in browser mode")
    parser.add_argument("--json", action="store_true", help="Print the complete report as JSON")
    parser.add_argument("--max-pages", type=int, default=30, help="Total page requests, including the product page (1–500)")
    parser.add_argument("--max-reviews", type=int, default=1000, help="Maximum unique valid reviews (1–10000)")
    parser.add_argument("--delay", type=float, default=MIN_DELAY, help="Seconds between all live requests, minimum 3")
    parser.add_argument("--business-id", type=int, help="Optional existing Laravel business ID; this is your explicit case-study assignment")
    parser.add_argument("--output", type=Path, help="New output directory; existing directories are never overwritten")
    parser.add_argument("--html", type=Path, nargs="+", help="Parse saved HTML files in order instead of fetching live pages")
    args = parser.parse_args(argv)
    fetcher = None
    try:
        url = validated_url((args.url or input("Paste the Jumia Nigeria product URL: ")).strip())
        if not 1 <= args.max_pages <= 500 or not 1 <= args.max_reviews <= 10000:
            raise CollectionError("Use --max-pages 1–500 and --max-reviews 1–10000.")
        if args.business_id is not None and args.business_id < 1:
            raise CollectionError("--business-id must be a positive existing business ID.")
        output = args.output or COLLECTIONS_ROOT / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        if output.exists():
            raise CollectionError(f"Output directory already exists: {output}. Choose a new one.")
        if args.html:
            saved_pages = iter(args.html)

            def fetch(target: str) -> str:
                try:
                    path = next(saved_pages)
                except StopIteration:
                    raise CollectionError("More pages were linked than supplied with --html; saved available results.") from None
                return path.read_text(encoding="utf-8")
        else:
            contact = args.contact
            if not contact and sys.stdin.isatty():
                contact = input("Bot owner contact email or URL: ").strip()
            fetcher = BrowserPageFetcher(contact, args.delay, args.headed) if args.transport == "browser" else PageFetcher(contact, args.delay)
            fetch = fetcher.get
        fetch_page = fetch
        page_number = 0

        def fetch_with_progress(target: str):
            nonlocal page_number
            page_number += 1
            if not args.json:
                print(f"Reading page {page_number}: {target}", flush=True)
            return fetch_page(target)

        dataset = collect(url, fetch_with_progress, args.max_pages, args.max_reviews)
        dataset["collection_mode"] = "saved_html" if args.html else f"{args.transport}_response"
        if fetcher and fetcher.captures:
            dataset["source_manifest"] = "sources/manifest.json"
        report = export_dataset(dataset, output, args.business_id)
        if fetcher:
            save_source_captures(fetcher.captures, output)
        if args.json:
            print(json.dumps({"output": str(output.resolve()), **report}, ensure_ascii=False, indent=2))
        else:
            coverage = report["coverage"]
            print(f"Saved {coverage['review_count']} unique reviews across {coverage['observed_weeks']} observed weeks.")
            print(f"Dates: {coverage['earliest_review'] or 'none'} to {coverage['latest_review'] or 'none'}")
            print(f"Output: {output.resolve()}")
            for filename in report["import_files"]:
                print(f"Import file: {output.resolve() / filename}")
            if report["error"]:
                print(f"Collection stopped: {report['error']}", file=sys.stderr)
            elif report["limit_reached"]:
                print("Stopped at the configured page/review limit; more reviews may be available.")
        return 1 if dataset["error"] or not dataset["reviews"] else 0
    except EOFError:
        print("Collector error: provide --url, or run in a terminal to paste the URL when prompted.", file=sys.stderr)
        return 1
    except (CollectionError, OSError, ValueError) as exc:
        print(f"Collector error: {exc}", file=sys.stderr)
        return 1
    finally:
        if fetcher:
            fetcher.close()


if __name__ == "__main__":
    raise SystemExit(main())
