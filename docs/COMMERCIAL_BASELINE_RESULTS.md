# Commercial baseline and matched sentiment experiment

**Follow-up:** The [commercial release](COMMERCIAL_RELEASE.md) adds external
human-label sentiment validation, four later test weeks and application
integration. The initial experiment below is retained as the record of baseline
selection; its already inspected test is not a fresh evaluation set.

Completed **13 November 2026**. We now have a financial baseline, an original
matched order/review dataset, scored text, fitted regression weights and a
reproducible chronological evaluation. The application still uses its existing
review forecasts. No commercial model has been promoted into user dashboards.

## What the baseline means

A baseline is the forecast a more elaborate model must improve upon. The
[standard naive, mean and drift methods](https://otexts.com/fpp3/toolbox.html)
provide useful simple comparisons. Selecting model parameters on earlier
validation periods and evaluating on later periods separates model selection
from its test. It does not establish guaranteed future accuracy.

There are two separate targets here. They are not pooled or compared as if they
shared a currency, time scale or business definition.

## Buffer: available financial-history benchmark

The existing collection supplies 32 monthly reports. Buffer explicitly
[changed its recognition of cancellations in August 2025](https://buffer.com/shareholders/august-2025),
so we evaluate the earlier definition and exclude the later regime rather than
pretend that the reported drop was purely a business decline.

Forecast origin: first day of each target month. Only earlier-published reports
are eligible. Same-day publication is excluded because release times are unknown.
Drift accounts for calendar gaps and publication lag. Targets July–December 2024
select the method; January–July 2025 provide seven later test targets. Earlier
test-month reports may enter later forecasts once published.

| Method | Validation MAE (USD) | Test MAE (USD) | Test WAPE |
|---|---:|---:|---:|
| Last published MRR | 48,063 | 72,400 | 3.96% |
| Mean of last three published MRR reports | 61,140 | 107,353 | 5.87% |
| Calendar-aware local drift, selected on validation | 16,995 | 17,773 | 0.97% |

The target is **monthly recurring revenue**, not accounting sales, cash or profit.
Seven test targets from one company are a limited initial benchmark. Reported
publication dates and historical text revisions are not independently verified.
The 14 captured Buffer reviews still yield only two aligned monthly examples,
so we have not fitted a Buffer sentiment-enhanced model.

Reproduce:

```sh
.venv/bin/python NLP_Service/scripts/evaluate_commercial_baseline.py --financials Scraper/data/collections/open-startups-2026-11-11/buffer-financials.json --output NLP_Service/evaluation/results/commercial-2026-11-13/buffer-baseline.json
```

## Olist: supporting data that meets the matching requirement

We downloaded the original [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
version 2, directly through Kaggle's public API. Its metadata describes real,
anonymised commercial orders and customer surveys. Licence: **CC BY-NC-SA 4.0**,
for non-commercial research with attribution and share-alike conditions.

This source supplies the relationship missing from the Buffer collection:
reviews link to orders, orders link to priced items, and both have timestamps.
It is a stronger fit for an e-commerce forecasting experiment than loosely
matching global SaaS finances to a handful of selected mobile-app reviews.
International data is usable for this development experiment; it does not need
to wait for Nigerian financial data. Claims remain tied to the data evaluated.

- 99,441 orders, 112,650 item rows and 103,886 payment rows.
- 99,224 review rows, representing 98,410 distinct survey IDs.
- 814 duplicate review rows collapsed. 55 reviews with impossible timing excluded.
- 42,326 valid unique reviews with text overall; **37,698** within the study window.
- **82 complete weeks**, 2 January 2017 through 29 July 2018.
- All 37,698 eligible texts scored. There are 33,103 distinct cleaned texts;
  identical text reuses an inference while genuine unique reviews still count.

The target is **next week's approved merchandise value in BRL**: item prices
assigned to approval week, excluding freight. This is a commercial outcome,
not a forecast of future reviews. It is gross order value and does not recover
Olist's commission revenue, net sales after refunds, profit or cash receipts.
It covers Olist-store activity across participating sellers, not one company
per seller or a specific Nigerian business.

Each child table is aggregated independently before joins. Otherwise, multiple
items, payments and reviews could multiply the same sale. Payment totals are
audited separately: 98,362 of 98,665 item-bearing orders with payment records
reconcile within BRL 0.01 to items plus freight. The remainder are retained as
reported differences, not silently forced to agree.

Review availability uses the **answer timestamp**, not order date or survey
creation. Stars remain separate from text scores. No-review periods are not
turned into observed neutral sentiment. Final delivered/cancelled status is not
used to retrospectively filter an approval-based outcome. The sparse launch and
terminal extract periods are excluded rather than treated as economic events.

## Text scores and fitted forecasting models

The pinned CardiffNLP XLM-R model scores Portuguese text through its general
multilingual route. [Portuguese is among its sentiment fine-tuning languages](https://huggingface.co/cardiffnlp/twitter-xlm-roberta-base-sentiment).
There is no translation, Pidgin routing, star-derived training label or lexicon
fallback. The compound score is the winning label's confidence, positive or
negative according to that label, and zero for neutral. These are model outputs,
not human sentiment annotations or calibrated satisfaction probabilities.

The sentiment network was **not retrained**. We trained forecasting regression
coefficients using those scores and historical commercial outcomes. The pretrained
text model postdates the transactions; this is a retrospective feature experiment,
not a claim that the exact model existed in 2017.

All models predict the same next-week outcome on the same dates:

1. Financial history: recent item-value and approved-order-count history.
2. Review-volume control: the same history plus lagged counts of text reviews.
3. Sentiment: the same control plus lagged compound means and negative share.

Four closed weeks supply features. The resulting 78 feature/target rows consist
of 48 initial training weeks, 13 validation weeks (January–March 2018) and 17 test
weeks (April–July 2018). Training expands at each origin. Earlier test outcomes
can enter later fits after their weeks close. This is one-week-ahead evaluation,
not a single 17-week forecast.

Ridge regression fits log(1 + outcome). Training-only medians, centers and scales
handle predictors. Missing indicators distinguish absent sentiment from an
observed score. Penalties 0.1, 1, 10 and 100 are selected by validation MAE only.
Naive, rolling-mean and local-drift financial methods are also compared on
validation. History-only ridge was the selected financial benchmark.

## Held-out results

| Model | Selected ridge penalty | Test MAE (BRL) | Test RMSE (BRL) | Test WAPE |
|---|---:|---:|---:|---:|
| Financial history | 0.1 | 44,890 | 57,845 | 21.01% |
| History and review volume | 1.0 | 40,708 | 53,154 | 19.05% |
| History, volume and text sentiment | 0.1 | 41,423 | 57,620 | 19.39% |

Sentiment improves MAE by **7.72% over financial history alone**, but its MAE is
**1.76% worse than the review-volume control**. It also loses to that control
on validation. Thus this experiment has **not established additional predictive
value from the text sentiment features beyond review counts**. Do not claim
that sentiment caused growth or that the model guarantees a percentage accuracy.

The result is retained without tuning repeatedly on the test weeks. It is a
useful research finding: volume explains some of the improvement that could
otherwise be wrongly attributed to sentiment. The sentiment model remains a
research candidate and has not replaced application forecasts.

## Reproduction and next experiments

See the [dataset notes](../Scraper/data/collections/olist-2026-11-13/DATASET_NOTES.md)
for collection, preparation, offline scoring and evaluation commands. The
[fixed protocol](../NLP_Service/evaluation/COMMERCIAL_PROTOCOL.md) gives the
selection rules. Outputs are local and ignored by Git:

- `NLP_Service/evaluation/results/commercial-2026-11-13/buffer-baseline.json`:
  per-origin predictions, available-report dates, selection and error metrics.
- `NLP_Service/evaluation/results/commercial-2026-11-13/olist-experiment.json`:
  per-origin predictions, prepared predictors, fitted research weights, input/code
  hashes, model revision and library versions.
- `Scraper/data/collections/olist-2026-11-13/`: unchanged original archive,
  source manifest/checksums, preparation audit, valid feedback and scored outputs.

Next development can inspect Portuguese sentiment errors with independent human
annotations, use earlier development folds to examine longer response lags, and
prepare carefully attributed seller/category panels. Multi-seller reviews must
not simply be copied into every business. Any further test of improved models
needs a new untouched period/business split or nested chronological evaluation.
The exposed April–July 2018 results are now a known benchmark, not a fresh test.

Static extract values and text may have been revised; timestamps lack timezone
metadata; selection into Olist and into survey responses is not random. There
are 17 dependent weekly test outcomes from one store aggregate. No cross-business
generalisability, causal effect, Nigerian accuracy or profit forecast has been
established. These limits do not prevent continued development on this dataset.

Verification: Python service and scraper suites passed **133 tests**, with two
optional browser tests skipped. New checks cover joins, source tampering,
publication/answer-time boundaries, missingness, no future-outcome selection,
training-only scaling and same-date comparisons.
