# Open-startup data collection — 11 November 2026

This is a new external business-data research collection, separate from the Nigerian Jumia product cases. It is not a trained or deployed commercial forecasting model.

## What was actually collected

| Source | Retained data | Status |
| --- | --- | --- |
| Buffer shareholder archive | 32 individually identified monthly reports, January 2023–December 2025 | Dates, MRR, ARR, customer counts and other explicitly labelled metrics parsed |
| Buffer US Apple App Store pages | 14 distinct dated review IDs from the product and linked review page | Selected visible sample; not complete review history |
| Ghost about page | One current snapshot with annual/monthly run rate, churn and customers | No historical monthly series established |
| Baremetrics open-startup directory | Five linked dashboard candidates | Discovery only; their financial histories have not been verified |
| Trustpilot | Crawler-rule snapshot and access outcome | Collection disallowed; no reviews downloaded |
| Capterra / G2 | Crawler policies and failed request evidence | Review requests returned 403; no bypass attempted |
| TrustRadius | Failed crawler-policy request | Policy request returned 403; review page not fetched |

Buffer's archive links include an annual 2023 report and a combined April/May 2023 report. These were not split into invented monthly records. The 32 retained single-month observations leave April, May, November and December 2023 missing. September/Q3 2024 is explicitly named as a month and includes a quarter summary; that mixed context is flagged. All retained financial rows have a reported publication date. The August 2025 MRR-calculation change is flagged.

MRR and ARR are recurring run-rate metrics, not cash collections or actual sales. Values are retained as decimal strings with the source's displayed value. The first conservative parser extracts one explicitly worded monthly revenue value (December 2025); it does not silently treat MRR or annual revenue as monthly sales. Other reported financial metrics retain their labels; their exact period/definition must be reviewed before choosing additional targets.

## Feedback scoring and alignment

All 14 feedback records were scored using the cached pinned general/Pidgin model configuration and the existing preprocessing/scoring code. In this sample all 14 used the general route: three positive, eight negative and three neutral predictions. These are model outputs, not human reference sentiment labels or a validation of Pidgin review accuracy. Processed files omit reviewer names; original captures may retain public bylines.

The selected reviews range from July 2014 to October 2026. Four reviews fall within the financial-history range, across October 2023, February 2024 and February 2025. With the forecast origin set to the first of each target month, prior-month feedback, and only financial reports published on an earlier date, there are **two paired target periods: March 2024 and March 2025**. The October 2023 feedback has no November 2023 monthly target record.

That is inadequate for a credible sentiment-based forecasting experiment. No revenue/MRR forecaster was trained, no model was promoted and no existing dashboard data was imported or modified. The collection is deliberately marked `not_trained`. More historical customer feedback matching the financial periods is required, followed by a declared chronological evaluation protocol.

## Timing and representativeness

- Publication dates are the dates stated in the reports, not verified historical publication timestamps or archived vintages. Same-day reports are conservatively excluded from a forecast origin because their release time is unknown.
- App dates are retained as provided, with their UTC offsets. Current text may contain edits that did not exist at a historical forecast origin. Original historical text versions are not verified.
- The Apple sample is selected, incomplete and specific to the US storefront. Storefront is not proof of customer residence, nationality or a paid subscription. Free and paid users are not distinguished.
- Missing monthly feedback produces missing sentiment, not neutral sentiment or zero total customer feedback.
- Global subscription-software outcomes do not establish prediction accuracy for Nigerian online retailers. No unrelated Nigerian economic series or Jumia product reviews were attached to these outcomes.
- Founder reports supply financial facts. Their narrative tone, company replies and review-site AI summaries are not treated as customer sentiment.

## Files

- `buffer-financials.json`: 32 monthly financial records and publication metadata.
- `buffer-feedback.raw.json`: 14 processed source reviews, IDs, text, dates and stars.
- `buffer-feedback.scored.json`: predictions, model revisions, preprocessing/model code hashes and cache fingerprint.
- `buffer-monthly-panel.json`: target/feature alignment with dates and explicit missingness.
- `collection-report.json`, `readiness-report.json`: actual coverage and the training-readiness result.
- `ghost-current-snapshot.json`, `baremetrics-directory-candidates.json`, `source-context-audit.json`: other-source discoveries without fabricated histories.
- `additional-review-source-audit.json`: collection outcomes for Capterra, G2 and TrustRadius.
- `sources/manifest.json`: request URLs, status codes, capture timestamps, original paths and SHA-256 checksums. Failed responses are retained as evidence, not parsed into data.
- `checksums.json`: artifact checksums, excluding itself.

The dataset and captures are ignored by Git; this note and the collector/tests are versioned. Keep source captures local when sharing only the processed research evidence.

## Reproduction

From the project root, replay existing source captures without network requests:

```sh
.venv/bin/python Scraper/open_startups.py \
  --snapshot Scraper/data/collections/open-startups-2026-11-11
.venv/bin/python NLP_Service/scripts/prepare_open_startups.py \
  --snapshot Scraper/data/collections/open-startups-2026-11-11
```

For a new source vintage, choose a fresh snapshot directory and add `--collect`; source downloads obey the current crawler rules with a minimum three-second request interval per host. `--audit-review-sources` checks the additional known review sources. Existing captured successful URLs are replayed, not silently refreshed. Source checksums are verified on replay. Financial-source parser assumptions and review IDs have regression tests in `Scraper/tests/test_open_startups.py`.

Add `--score` to the preparation command to score a new snapshot using the required local model caches. Subsequent runs reuse the matching score cache; changed text/model inputs require a separate preserved snapshot. Model weights are not downloaded by this preparation step.

Public source entry points:

- https://buffer.com/shareholders
- https://buffer.com/shareholders/december-2025
- https://apps.apple.com/us/app/buffer-plan-schedule-posts/id490474324
- https://ghost.org/about/
- https://baremetrics.com/open-startups

Crawler-policy evidence and canonical review-page redirects are preserved with the captures. This collection does not establish licensing or availability of a comprehensive review export.
