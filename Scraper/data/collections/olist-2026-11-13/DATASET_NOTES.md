# Olist matched commercial research collection

Publisher: **Olist**. Source: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
Kaggle dataset `olistbr/brazilian-ecommerce`, **version 2**. Downloaded directly
through the public Kaggle API on 13 November 2026, without credentials or a
third-party mirror. Source licence: **CC BY-NC-SA 4.0**. Academic non-commercial
use, attribution and share-alike apply. Raw files and model outputs remain local
and are ignored by Git. This note is versioned.

The source describes real, anonymised Olist-store orders across Brazilian
marketplaces. Store/partner references in text have been anonymised. This is a
historical development dataset; it is not new Nigerian customer data. Its strong
advantage over the Buffer sample is the explicit review-to-order relationship.

## Records and preparation

- 99,441 orders, 112,650 item rows, 103,886 payment rows and 99,224 review rows.
- 98,410 distinct review IDs. Collapse 814 duplicate rows, retaining associated
  order IDs; exclude 55 reviews with impossible response timing. No conflicting
  duplicate review IDs were found in this release.
- 42,326 distinct valid reviews have text. Of these, 37,698 fall in the declared
  82-week study window, 2 January 2017–29 July 2018.
- Exclude 14 orders with items but no approval timestamp from the approval-based
  outcome. No approval-before-purchase cases were found among item-bearing orders.
- All 98,665 item-bearing orders with payment records are checked independently:
  98,362 reconcile within BRL 0.01 to items plus freight. The largest discrepancy
  is BRL 182.81. Payments are retained for audit, not substituted for item value.

Outcome: **approved merchandise value in BRL**, sum of item prices in the order's
approval week, excluding freight. It is gross order value. Final status is not
used as a retrospective filter. Refunds, cancellations, fees, costs and profits
are not reconstructed. Olist's own revenue and each seller's net earnings are
not supplied by this outcome.

Review availability is `review_answer_timestamp`, not purchase date or survey
creation. Preserve source stars independently from text. Identical survey IDs
are counted once even if linked to multiple orders. Child tables are aggregated
before joining to prevent multiplication of order values.

Source timestamps lack an explicit timezone. Amount/text revisions and historical
database vintages cannot be verified from this static release. The sparse launch
and terminal periods are excluded. Never label the final near-empty extract as
a real business collapse. The aggregate covers several sellers and products.

## Files

`source-manifest.json` records original metadata, pinned download URL, capture
time, licence, version and SHA256 checksums. `olist-original.zip` is the unchanged
source release; only the six required CSVs are extracted. Geolocation and customer
address tables are not extracted or used.

`weekly-panel.json` holds exact decimal BRL target totals and feedback coverage.
`reviews.prepared.json` retains valid deduplicated surveys, including those with
no text. `reviews.experiment.json` contains all 37,698 eligible text records.
`readiness-report.json` records exclusions, coverage and reconciliation.

`reviews.sample.json` is a deterministic, rating-independent sample of up to 32
reviews per week (2,567 records) for a scoring smoke test. Main forecast results
use **all** eligible text records in `scoring-full/reviews.scored.json`, not this
sample. Repeated cleaned text can share an inference result, but distinct review
IDs retain their individual weight in feedback aggregates.

Scoring uses the pinned local CardiffNLP multilingual XLM-R model, which includes
Portuguese in its sentiment training. Explicit multilingual routing avoids false
Pidgin detection. Compound score uses signed winning-label confidence, with
neutral set to zero, matching the application's definition. These scores are
model predictions, not human sentiment labels or calibrated satisfaction scores.
The pretrained model postdates the source transactions. The experiment is a
retrospective study, not a claim of deployment in 2017.

## Reproduction

From the project root:

```sh
.venv/bin/python Scraper/olist.py --snapshot Scraper/data/collections/olist-2026-11-13 --collect
.venv/bin/python Scraper/prepare_olist.py --snapshot Scraper/data/collections/olist-2026-11-13
.venv/bin/python NLP_Service/scripts/score_olist.py --snapshot Scraper/data/collections/olist-2026-11-13 --full --batch-size 16
.venv/bin/python NLP_Service/scripts/evaluate_olist.py --snapshot Scraper/data/collections/olist-2026-11-13 --output NLP_Service/evaluation/results/commercial-2026-11-13/olist-experiment.json
```

Only initial collection uses the network. Subsequent collection calls verify the
saved original checksums. Scoring requires the existing pinned local model cache,
fails if it is unavailable, and has no silent lexicon fallback. It checkpoints
completed text scores and refuses changed model/input identities in the same run.

See `NLP_Service/evaluation/COMMERCIAL_PROTOCOL.md` for fixed temporal splits,
features, selection and evaluation. This collection is kept separate from the
application's user accounts and Jumia reviews.
