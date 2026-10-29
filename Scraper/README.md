# Jumia Nigeria review collector

## Quick start

From the project root:

```bash
.venv/bin/python Scraper/jumia_reviews.py
```

The script asks for a **Jumia Nigeria product URL**, opens a browser session, selects the response containing review HTML, follows the full-review link and pagination, and exports the results. The default limit is 30 page navigations and 1,000 unique valid reviews. A reached limit is reported explicitly.

The bot owner contact previously supplied for this project is stored in the ignored `Scraper/.env`. For another checkout, copy `.env.example` to `.env` and set `JUMIA_SCRAPER_CONTACT`. Environment variables and `--contact` override that local value. An interactive live run asks for a contact if none is configured. The contact is sent to Jumia in the identified bot User-Agent and is not included in the dataset.

## Setup

```bash
.venv/bin/python -m pip install -r Scraper/requirements.txt
.venv/bin/python -m playwright install chromium
```

Headless-only setups can install `chromium --only-shell`. Install full Chromium to use `--headed`.

## Response capture

The browser observes document responses and review-related XHR/fetch responses. It selects successful HTML containing review cards, an explicit zero-review state, or the full-review link. HTML fragments nested in JSON responses are supported. A full-review response takes priority over a product-page preview. Arbitrary JSON arrays are not interpreted as reviews.

Jumia can serve reviews in the HTML document itself; a separate JSON review API is not assumed. The code uses Playwright's documented [network response events](https://playwright.dev/python/docs/network) and [response bodies](https://playwright.dev/python/docs/api/class-response).

The selected response URL and HTML are retained. Original text/dates/ratings are preserved, duplicate fingerprints are removed within the run, and actual pagination links are followed. No sentiment labels, language labels, sales figures, or missing dates are invented.

## Command-line options

```bash
.venv/bin/python Scraper/jumia_reviews.py \
  --url 'https://www.jumia.com.ng/ACTUAL-PRODUCT-PAGE.html' \
  --max-pages 30 \
  --max-reviews 1000
```

- `--transport browser`: browser response capture; the default.
- `--transport http`: the original direct HTTP collector.
- `--headed`: show Chromium; browser mode only.
- `--contact EMAIL_OR_URL`: override the configured contact.
- `--business-id 7`: explicitly assign records to an existing Laravel business ID; seller attribution is not inferred.
- `--output NEW_DIRECTORY`: choose a new collection directory. Existing directories are never overwritten.
- `--delay SECONDS`: at least three seconds between content requests, increased for a published crawl delay.
- `--max-pages N`: up to 500 page navigations for larger review histories; the default remains 30.
- `--max-reviews N`: up to 10,000 unique valid reviews; the default remains 1,000.
- `--json`: print the full report instead of a short summary.

The example URL is a placeholder. The collector accepts HTTPS product/full-review URLs on Jumia Nigeria, not store-wide inventory crawling.

## Output

New runs go under `Scraper/data/collections/<UTC timestamp>/`.

| File/folder | Purpose |
| --- | --- |
| `reviews.raw.json` | Processed records, provenance, exclusions, status, and coverage |
| `import-001.json` | Dashboard-compatible import; more files contain further batches of at most 1,000 records |
| `report.json` | Dates, reviews per week, ratings, source/limit information, and errors |
| `sources/` | Selected response HTML and its source manifest |

The [first real itel dataset](data/collections/itel-power-station/DATASET_NOTES.md) and its captures are together under `data/collections/itel-power-station/`. Earlier failed pilots and the verification replay are in `data/archive/`. Generated data is ignored by version control.

The [second real Nivea dataset](data/collections/nivea-dry-impact/DATASET_NOTES.md) contains 1,532 unique review fingerprints from all 155 listing pages. Its two import batches preserve actual dates and stable IDs. The dataset notes include exact coverage, limitations and an offline replay command.

Source HTML can contain public reviewer bylines. Processed records have no separate reviewer-name field; bylines contribute to fingerprints when native IDs are unavailable. Identical same-day submissions with the same byline may be merged. Keep source captures local when sharing only processed data.

Reviews with missing/invalid dates, ratings, or text are retained as exclusions and omitted from imports. Errors preserve earlier results. Failed/partial runs and runs with no usable reviews exit nonzero. Check both `status` and `limit_reached` before using a dataset.

## Import into Pulseboard

Select/create a separate case-study business for the product, choose `import-001.json`, and keep artificial date spreading disabled. Import each further numbered batch into that same business. New exports retain stable `source_review_id` values; the updated backend skips repeated IDs within the same business. The original itel import predates those IDs and should still be imported only once. Retain raw records, report and sources as provenance; source URLs remain in the raw export.

Actual customer ratings are separate from sentiment-derived scores. Product reviews do not establish seller-specific sales or which seller fulfilled each purchase.

## Saved HTML

```bash
.venv/bin/python Scraper/jumia_reviews.py \
  --url 'https://www.jumia.com.ng/ACTUAL-PRODUCT-PAGE.html' \
  --html /absolute/path/product.html /absolute/path/reviews.html \
  --max-pages 2 \
  --output Scraper/data/collections/saved-pages-pilot
```

Supply files in traversal order: product, full-review page, then next pages. No browser, contact, or network is needed. The URL provides provenance and resolves links. An unsupplied linked page creates a partial-run error; a page limit can intentionally stop traversal.

The itel dataset notes include its exact replay command.

## Network behaviour and verification

Live transports read current `robots.txt` and stop when collection is disallowed. Browser mode blocks unrelated APIs, ads, and media. It does not solve challenges, rotate identities, or bypass access failures. HTTP 401/403/410/429 from document/review responses stops collection. Followed content requests and redirects are checked against current rules.

The [published Jumia crawler instructions](https://www.jumia.com.ng/robots.txt), inspected on 29 October 2026, require an identified bot owner and fewer than 200 requests per minute. The default delay limits sequential content requests to at most 20 per minute.

Earlier direct HTTP checks returned 410, while the in-app browser accessed the supplied itel product and its 21 review pages. The preserved 201-review dataset came from that browser and was replayed through the saved-HTML parser. This does not guarantee acceptance of every new Chromium session; inspect the current report for live results.

The new local Chromium response-capture mode was checked on the same itel URL on 29 October 2026 and also received HTTP 410. It stopped and retained a failed-run report under `data/archive/browser-response-validation-2/`. Response selection, pagination, and stopping on access blocks have additionally been verified in a real Chromium session using locally supplied HTTP responses, without live Jumia requests.

```bash
.venv/bin/python -m pytest Scraper/tests -q
```

Tests cover parsing, provenance, exclusions, prompts, response selection, JSON-wrapped HTML, pagination, deduplication, robots rules, access failures, batches, and saved-page export. Mocked tests establish behaviour; live collection and model accuracy need separate verification.

Run the two opt-in Chromium integration tests after installing the browser:

```bash
FYP_RUN_BROWSER_TESTS=1 .venv/bin/python -m pytest Scraper/tests/test_browser_integration.py -q
```
