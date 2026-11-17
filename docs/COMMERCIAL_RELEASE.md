# Sentiment validation and commercial forecasting release

Implemented and tested **13 November 2026**. Sentiment remains part of the
project and an explicit input to the displayed commercial forecast. The target
is **next-week approved merchandise value**, excluding freight. It is a gross
order-value measure, not profit, cash or net revenue after refunds.

## Sentiment validation

We evaluated the existing frozen multilingual classifier against independently
published **human annotations** from [RePro](https://aclanthology.org/2024.propor-1.44/),
an e-commerce sentiment corpus derived from B2W reviews. The author-hosted
[release](https://huggingface.co/datasets/lucasnil/repro) was downloaded at revision
`cb93d9cc1183d4a594317a5188d325bcaa04cda4`. This is an external Portuguese review
benchmark, not newly invented labels or customer stars used as sentiment truth.

The actual release CSV contains 10,003 rows. We excluded 2,018 mixed-polarity
records because the existing classifier has three classes and cannot represent
mixed positive/negative sentiment as a fourth class. Mixed reviews were not
relabelled neutral. We also excluded five exact cleaned-text Olist overlaps and
five duplicate texts. **7,975** distinct eligible texts remained.

| Measure | Result |
|---|---:|
| Accuracy | 91.49% |
| Macro-F1, three classes | 0.803 |
| Balanced accuracy | 89.10% |
| Majority-class accuracy baseline | 51.75% |

| Human reference class | Support | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Negative | 3,449 | 97.62% | 86.63% | 0.918 |
| Neutral | 399 | 36.75% | 84.46% | 0.512 |
| Positive | 4,127 | 99.35% | 96.22% | 0.978 |

The classifier overuses neutral, including 445 human-negative and 135
human-positive reviews. Positive and negative predictions are much stronger
than neutral precision. This limitation matters when interpreting zero compound
scores. These results support continued Portuguese e-commerce experimentation;
they do not establish Olist-specific, English or Nigerian Pidgin accuracy.
Exact overlap removal cannot prove the absence of related upstream pretraining
text. No thresholds or network weights were tuned on this benchmark.

The source README frontmatter says CC-BY-4.0, while its explicit Licensing
section and the paper require **CC BY-NC-SA 4.0**, attribution to B2W Digital,
and non-commercial use. We follow the stricter explicit terms. Raw corpus files
and scored outputs remain local and ignored by Git.

Reproduce from the project root:

```sh
.venv/bin/python NLP_Service/scripts/validate_repro.py --snapshot Scraper/data/collections/repro-2026-11-13 --olist Scraper/data/collections/olist-2026-11-13 --collect
.venv/bin/python NLP_Service/scripts/score_olist.py --snapshot Scraper/data/collections/repro-2026-11-13 --full --batch-size 16
.venv/bin/python NLP_Service/scripts/validate_repro.py --snapshot Scraper/data/collections/repro-2026-11-13 --evaluate
```

The final command writes `validation-report.json`, including the confusion
matrix, exclusions, reference counts, model revision, weight hash and source
checksums. The classifier sees only text, never reference labels or stars.

## Additional forward evaluation

The earlier April–July 2018 forecast test is known and was not reused to tune
another model. We declared [a forward protocol](../NLP_Service/evaluation/COMMERCIAL_FORWARD_PROTOCOL.md)
before calculating errors for four additional complete weeks: **30 July,
6 August, 13 August and 20 August 2018**. We retained the same features and
penalties selected earlier. The incomplete terminal week beginning 27 August
was excluded from actual-outcome evaluation.

The extended collection contains **86 complete sales weeks and 41,110 scored
text reviews**. It uses the same original Olist v2 archive, not a mirror or a
different fabricated financial history. Earlier genuine reviews keep their
individual weights; identical cleaned text can reuse verified model inference.

| Model | Four-week MAE (BRL) | RMSE (BRL) | WAPE |
|---|---:|---:|---:|
| Financial history | 44,388 | 47,513 | 18.63% |
| History and review counts | 45,008 | 49,761 | 18.89% |
| History, counts and sentiment | 45,888 | 49,371 | 19.26% |

Sentiment stays in the project, but these results still **do not establish
additional predictive benefit from text sentiment**. The forecast controls and
their errors remain visible. We did not manufacture an improvement or tune on
these four outcomes after seeing their errors.

Ranges use only earlier prequential errors: the last 20 absolute log errors,
with at least 12 required. A conservative upper order statistic gives a nominal
90% range, transformed back into currency. Temporal dependence prevents a
distribution-free coverage guarantee. The sentiment ranges covered **4 of 4**
new outcomes, with mean width approximately **BRL 241,974**. They are wide; four
covered outcomes are not evidence of 100% future accuracy or precise forecasts.

This is a temporal extension of **one store aggregate**, not a new independent
company. Stronger cross-business evidence remains future research, not a release
claim. The untouched-period check requested for this prototype is complete.

Reproduce:

```sh
.venv/bin/python NLP_Service/scripts/prepare_commercial_forward.py --source Scraper/data/collections/olist-2026-11-13 --output Scraper/data/collections/olist-forward-2026-11-13
.venv/bin/python NLP_Service/scripts/score_olist.py --snapshot Scraper/data/collections/olist-forward-2026-11-13 --full --batch-size 16 --reuse-cache Scraper/data/collections/olist-2026-11-13/scoring-full/reviews.scored.json
.venv/bin/python NLP_Service/scripts/evaluate_commercial_forward.py --snapshot Scraper/data/collections/olist-forward-2026-11-13 --output NLP_Service/evaluation/results/commercial-2026-11-13/forward-check.json
```

## Application behavior

The new commercial forecast is separate from the existing review-count and
star-rating forecasts. It appears automatically on business and product
dashboards, with an actual-history line, a dashed one-week forecast, an estimated
range, historical errors, data cutoff and generation time. Pointer, touch and
keyboard figures share the existing chart interaction code. Historical chart
points open that week's reviews; the forecast point does not imply reviews exist.

Sales imports belong to **product dashboards**. The business dashboard combines
product records only when every product has financial data, the weeks overlap,
and currencies agree. Partial product periods are counted and excluded from
the common window. Missing internal weeks block forecasting instead of silently
becoming zero. Mixed currencies are not added or converted automatically.

Requirements per forecast series:

- 28–520 consecutive, complete Monday–Sunday sales weeks. Four weeks create
  lagged predictors, twelve earlier feature/target pairs initialize fitting,
  and twelve subsequent past-only errors initialize uncertainty estimation.
- Explicit approved item value and approved order count in one currency.
  Genuine zero weeks are allowed. Positive value with zero orders is rejected.
- Dated, scored reviews matching the sales history. Estimated demo dates are
  excluded. Earlier history and the latest four weeks must contain sentiment.
- Confirmed review collection coverage through the final sales week. This is
  needed to distinguish an actual no-review week from an incomplete collection.
- Quarterly totals are not divided into synthetic weeks. The current release
  accepts weekly totals only; quarterly models require a separate implementation.

The product model is a **locally refitted ridge regression with lagged
sentiment**. It uses the fixed public-development penalty rather than claiming
that public-store weights fit every business. Baselines remain diagnostics.
The primary commercial model does not silently drop sentiment. Local historical
errors are clearly described as diagnostics, not independent test accuracy.

Sales records retain currency, source, timestamps and exact two-decimal amounts.
Duplicate imports skip unchanged weeks. Conflicting totals reject the entire
batch transaction and preserve the prior history. Existing weekly totals cannot
be silently overwritten. Authentication middleware enforces product/business
ownership on every new endpoint. Cached forecasts are invalidated when the
actual sales or matched sentiment inputs change. Invalid service responses
preserve the previous stored estimate.

The larger live test exposed PHP's 128 MB limit when loading every review model
at once. Dashboard summaries now aggregate in the database; trend, outlook and
commercial calculations process reviews in bounded batches and retain only
weekly numeric totals. This fixes the full 41,110-review workflow without raising
the memory limit.

## Try it locally

```sh
.venv/bin/python scripts/dev.py
```

Open [the local app](http://127.0.0.1:8080/), choose **Use sales research demo**,
then **Sign in**. New-account credentials:

- Email: `commerce@pulseboard.test`
- Password: `PulseboardDemo!2026`

This separately named account contains the historical Brazilian Olist portfolio.
It does not replace the Jumia demo or populate another business with foreign
sales. Existing passwords and ownership are preserved on subsequent preparation.
The launcher loads this account when the prepared forward files exist. Other
checkouts must reproduce the local source/model files first.

The source ends 26 August 2018. The dashboard therefore labels its estimate for
27 August as a **historical snapshot**, not a current 2026 business forecast.
For real accounts, import their actual recent sales and matching reviews. The
original Jumia demo has no invented financial records and shows a sales-data
requirement instead.

## Verification evidence

- 138 Python service/scraper tests passed; two optional browser tests skipped.
- 73 Laravel tests passed, 516 assertions.
- Live API verification matched all **86** weekly values/order counts and all
  **41,110** response-week sentiment records to the original-derived files.
- Re-importing all 86 sales weeks created zero duplicates. A deliberately
  conflicting batch rolled back its new row and left the original history intact.
- Browser checks covered commercial login, actual/forecast chart figures,
  historical error comparison, product sales imports, and invalid-JSON feedback.
- `.logs/commercial-app-verification.json` retains the live numeric checks.

See [the previous experiment](COMMERCIAL_BASELINE_RESULTS.md) for initial
baseline selection and [the service contract](../Backend/NLP_SERVICE_CONTRACT.md)
for the new request/response boundary.
