# Nivea Dry Impact — second real product collection

Collected on **29 October 2026 (Africa/Lagos)** from the [product link supplied by the user](https://www.jumia.com.ng/nivea-dry-impact-roll-on-for-men-72h-50ml-pack-of-3-104325942.html) and its [linked review listing](https://www.jumia.com.ng/catalog/productratingsreviews/sku/NI930ST22E5UCNAFAMZ/).

## Collection results

- All **155** review pages were traversed by following their actual Next Page links, ending where no next page was offered.
- The written-review count stayed at **1,545** on every captured listing page, distinct from the **10,227** aggregate ratings displayed by the product.
- **1,532 unique review fingerprints** remain after removing **13** repeated entries across the review listing.
- Three product-page preview entries also matched listing reviews. The parser therefore reports **16 duplicates removed** across 1,548 parsed cards, including previews.
- **No exclusions** for invalid or missing original review dates, actual customer ratings, or review text.
- Review dates span **26 April 2022–27 October 2026**.
- Product SKU: `NI930ST22E5UCNAFAMZ`; public product-page identifier: `104325942`.
- The collection is complete for the visible paginated written-review listing at capture time; no page/review limit was reached.

| Actual customer stars | Unique reviews |
| --- | ---: |
| 1 | 28 |
| 2 | 23 |
| 3 | 64 |
| 4 | 261 |
| 5 | 1,156 |

These are original customer ratings, not sentiment labels. A review can express dissatisfaction while having a high star rating; those differences are preserved. At collection time this dataset had not been sentiment-scored, and no human reference labels were added. Later, all 1,532 records were imported and scored by the local application after its large-import recovery fix. These database predictions do not alter the preserved source/import files or supply human reference labels; see `../../../../docs/APP_VERIFICATION.md`. The existing curated Pidgin marker detector matches one review; that is not a reliable count of all Pidgin-language text.

## Historical coverage

The collection spans **236 calendar weeks**, including the current partial week. **212** weeks contain at least one visible review. At a 29 October 2026 cutoff:

- **235 completed calendar weeks**, compared with 36 in the itel pilot.
- **1,529 reviews** across **211 observed completed weeks**.
- **Three current-week reviews** should be excluded from forecast training and scoring.
- **24 completed weeks have no reviews in the captured listing**. Treat them as zero only under an explicit complete-collection assumption. Present-day completeness does not prove what reviews were visible historically.

| Review year | Reviews |
| --- | ---: |
| 2022 | 155 |
| 2023 | 89 |
| 2024 | 233 |
| 2025 | 513 |
| 2026 | 542 |

This supplies a longer second product history for subsequent forecasting experiments. It does not by itself establish improved accuracy. The sparse earlier period, changing review participation, and any historical changes to the listing remain relevant. Product reviews do not establish which seller fulfilled each purchase or represent the seller's entire business.

The current economic snapshot starts in December 2024. Economic-feature experiments cannot use it to invent exchange-rate observations for the earlier 2022–2024 review history. History-only and sentiment models can use longer eligible windows; comparisons with economics must use declared common eligible periods.

## Files and use in the dashboard

- `reviews.raw.json`: all deduplicated processed records, dates, stars, source URLs, IDs and collection metadata.
- `import-001.json`: first **1,000** records, compatible with Laravel's batch limit.
- `import-002.json`: remaining **532** records.
- `report.json`: collection summary and weekly/rating coverage.
- `verification.json`: replay, ID, date, source-chain and import checks.
- `checksums.json`: SHA-256 checksums for preserved artifacts, excluding the checksum file itself.
- `sources/`: source excerpts, per-page capture records, pagination journal, source manifest and the current robots-policy check.

Create/select a **separate Nivea product case-study business** in Pulseboard. Keep **Demo only: spread undated reviews** unchecked, and import both numbered files into that same business. New imports retain stable `source_review_id` values, so repeating them in the same business is skipped by the updated backend. Do not mix this product into the itel business. The existing dashboard sends review text to the local sentiment service when importing; the supplied files themselves remain unscored source data.

For forecast generation, use the collection cutoff of **2026-10-29** and select complete visible-review coverage only with the assumptions above. Sentiment/rating ground truth and seller sales records remain separate research tasks.

## Provenance and reproducibility

This was a **browser-assisted DOM capture** using the accessible in-app browser. Captures contain the actual review-card markup, original displayed dates, stars and pagination anchors. They are source excerpts rather than full original HTTP response bodies. The original Python parser processed those excerpts without fabricating missing values. Source captures retain public reviewer bylines to reproduce content fingerprints; processed exports contain no separate reviewer-name field. Identical entries with the same date, text, stars and byline can be merged, so fingerprints should not be described as verified distinct people.

Current crawler rules and their check are preserved in `sources/robots.txt` and `sources/robots-check.json`. A minimum three-second interval was applied between review-page navigations. The separate HTTP policy check used the configured identified collector contact; browser captures used the standard in-app browser session.

To replay through the collector from the project root, choose a new output directory:

```bash
.venv/bin/python Scraper/jumia_reviews.py \
  --url 'https://www.jumia.com.ng/nivea-dry-impact-roll-on-for-men-72h-50ml-pack-of-3-104325942.html' \
  --html Scraper/data/collections/nivea-dry-impact/sources/000-product.html Scraper/data/collections/nivea-dry-impact/sources/*-page-*.html \
  --max-pages 200 --max-reviews 10000 \
  --output Scraper/data/collections/nivea-reproduced
```

The default 30-page/1,000-review limits are intentionally overridden for this larger product history. The replay is offline and requires no additional requests to Jumia.
