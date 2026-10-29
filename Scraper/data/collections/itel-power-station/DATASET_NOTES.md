# First real review dataset: itel IESS-320T power station

Collected on **29 October 2026 (Africa/Lagos)** from the [Jumia Nigeria product supplied by the user](https://www.jumia.com.ng/itel-energy-100000mah-320wh-power-go-portable-power-station-130w-lifepo4-battery-iess-320t-419199930.html) and its [full review listing](https://www.jumia.com.ng/catalog/productratingsreviews/sku/IT724GP6OJ3RRNAFAMZ/).

## What was collected

- 205 displayed text-review entries across all 21 review pages.
- 201 unique review fingerprints after removing four repeated entries from those pages.
- Three additional product-page preview entries were also removed as duplicates. The collector therefore reports seven duplicates removed across 208 parsed cards.
- No exclusions for missing/invalid text, original dates, or ratings.
- Original review dates: **17 February–28 October 2026**.
- **35 observed weeks** within a 37-week calendar span. Weeks starting 9 and 16 March have no reviews in this collection.
- Product SKU: `IT724GP6OJ3RRNAFAMZ`; product page identifier: `419199930`.

| Actual customer rating | Unique text reviews |
| --- | ---: |
| 1 star | 2 |
| 2 stars | 3 |
| 3 stars | 9 |
| 4 stars | 28 |
| 5 stars | 159 |

These are customer star ratings, not human sentiment labels. The text-review subset is strongly skewed toward high ratings. Its distribution/mean need not equal the page's aggregate rating, which also includes ratings without review text. Do not treat the aggregate rating count as the number of collected text reviews.

## Collection and verification

The direct HTTP collector returned HTTP 410 for both the product and its actual linked review URL. The pages were accessible through the in-app browser without a challenge. Collection followed the displayed next-page links, with captured DOM excerpts saved locally. This is a **browser-assisted collection**, not a successful direct HTTP scrape.

The same Python parser processed the real captured HTML. It retained titles, bodies, original dates, and actual customer ratings. The resulting import was validated against the backend's supported field format. Replaying the saved HTML through the command-line collector reproduced the same 201 records. The collector's 28 offline tests also passed.

Source excerpts and their capture times are retained in `sources/manifest.json`. These excerpts retain public reviewer bylines for reproducibility; the processed raw dataset and import have no separate reviewer-name field. When no native review ID was exposed, product/date/rating/title/body/byline fingerprints were used for deduplication. Identical submissions with the same byline may therefore be merged; these are unique fingerprints, not verified distinct customers.

At the time of collection, no sentiment inference or forecast evaluation had been performed. Subsequently, all 201 reviews were scored with a pinned pretrained model and used in the separate offline backtest documented at `../../../../docs/BACKTEST_RESULTS.md`. The original raw/import files remain unchanged by scoring. Independent human sentiment annotation, database import, and sales/order/revenue records remain outstanding. Product reviews do not establish which seller fulfilled each purchase.

## Use in Pulseboard

Choose `import-001.json` in the existing batch import panel after selecting the intended case-study business. Use a name that makes the product-level scope clear, such as **Jumia — itel IESS-320T product case study**. Disable artificial spreading of undated reviews. Import the file only once; the existing backend does not deduplicate repeated file imports.

Keep `reviews.raw.json`, `report.json`, this note, and the source manifest as provenance. Preserve an untouched copy before further cleaning or annotation.

## Reproduce the import from the saved source excerpts

From the project root, choose an output directory that does not already exist:

```bash
.venv/bin/python Scraper/jumia_reviews.py \
  --url 'https://www.jumia.com.ng/itel-energy-100000mah-320wh-power-go-portable-power-station-130w-lifepo4-battery-iess-320t-419199930.html' \
  --html Scraper/data/collections/itel-power-station/sources/000-product.html Scraper/data/collections/itel-power-station/sources/*-page-*.html \
  --max-pages 30 \
  --max-reviews 1000 \
  --output Scraper/data/collections/itel-reproduced
```

## Implications for the next experiment

This supplies genuine dated review history for a prototype case study. It does not establish prediction accuracy or represent all Nigerian online businesses. Some weeks contain only one or two reviews, two weeks are unobserved, and the week starting 26 October is incomplete at collection time. Forecast evaluation should preserve those limitations, avoid inventing dates, and use only information available before each forecast date.

The next steps are to import and score the reviews, independently label an evaluation subset, and then compare forecasts on later complete weeks with a simple baseline. Keep genuine customer ratings separate from sentiment-derived scores.
