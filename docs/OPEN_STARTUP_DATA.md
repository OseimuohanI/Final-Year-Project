# Open-startup commercial-data milestone

**13 November update:** A publication-aware Buffer financial baseline and a
separate, matched Olist order-value/sentiment experiment have now been fitted and
evaluated. See [commercial baseline results](COMMERCIAL_BASELINE_RESULTS.md).
The Buffer feedback shortage described below remains; the new sentiment
experiment uses Olist's explicitly linked reviews and orders.

On 11 November 2026 the project obtained actual external business metrics as a possible basis for extending feedback forecasts to a commercial target. The dataset is separate from the research dashboard and has not changed its existing models or records.

See the [dataset notes](../Scraper/data/collections/open-startups-2026-11-11/DATASET_NOTES.md) for exact source, date, missingness and access details.

## Result

- Buffer: 32 monthly MRR records for individually identified months between January 2023 and December 2025, with reported publication dates, other explicitly labelled metrics and a flagged August 2025 definition change.
- Feedback: 14 distinct reviews captured from Buffer's linked public US App Store pages and scored with the existing pinned sentiment models. Four reviews overlap the financial range. They form only two eligible monthly forecast pairs after availability alignment.
- Ghost: one live metrics snapshot, not a historical training series.
- Baremetrics: five linked dashboard candidates recorded for further investigation, not verified outcome series.
- Other review access: Trustpilot disallowed collection; Capterra/G2 returned 403 and TrustRadius's crawler-policy request returned 403. These failures were retained rather than bypassed or filled with search summaries.

The collection demonstrates that actual commercial inputs can be acquired and that the existing text-scoring pipeline can process matching feedback. It does **not** provide sufficient matched history to fit and assess a sentiment-based revenue forecast. MRR is a recurring run rate, not accounting sales or profit, and these global businesses do not validate a Nigerian commercial-performance claim.

## Implementation

`Scraper/open_startups.py` collects or replays source pages, parses monthly facts, follows validated canonical redirects, deduplicates review IDs, retains provenance and audits source availability. It rejects combined/annual reports as single-month data and leaves unknown publication dates missing.

`NLP_Service/scripts/prepare_open_startups.py` loads the required local model revisions, scores text without substituting stars as sentiment labels, records input/code fingerprints and builds an availability-aware monthly panel. With a target-month forecast origin, previous-month feedback and only earlier-published financials become predictors. Target MRR is kept separate from the available-history fields. The resulting `readiness-report.json` explicitly says `not_trained`.

Tests cover financial definitions, dates, combined reports, quarter commentary, review-ID conflicts, exclusion of company replies/names from processed feedback, missing feedback, target leakage, checksums and redirect boundaries. Existing source files/models remain separate from this new collection.

## Next requirement

A substantially broader dated review/feedback history overlapping the financial periods is needed. A permitted historical review export, appropriate research-access dataset or another business with both accessible histories could supply it. A larger financial history alone does not fix the missing sentiment observations. No-feedback periods must not be manufactured as neutral examples.

Once that paired dataset exists, declare the target and chronological evaluation protocol before fitting. Compare outcome-history baselines against models with lagged sentiment, and evaluate across later periods and, for transfer claims, held-out businesses. Evaluate Nigerian businesses separately before making Nigeria-specific accuracy claims.
