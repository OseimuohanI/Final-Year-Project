# A practical route to completing your sentiment analysis project

Working topic: **Design and Implementation of a Sentiment Analysis System to Predict the Performance of an Online Business in Nigeria.**

Initial project review: 29 October 2026. No performance measure has been specified by the supervisor, and at the initial review you had no collected business dataset. The scope below is a proposal to discuss, not an approved research design.

**Data milestone completed:** your supplied Jumia itel IESS-320T product has yielded **201 unique review fingerprints**, dated **17 February–28 October 2026**, covering **35 observed weeks**. Collection used browser-accessible pages and the scraper's saved-HTML parser because direct HTTP returned 410. The import file is `Scraper/data/collections/itel-power-station/import-001.json`; its provenance and limitations are documented in `Scraper/data/collections/itel-power-station/DATASET_NOTES.md`. All reviews have now been scored with a pinned pretrained model. An offline retrospective backtest compared history, sentiment, and CBN exchange-rate inputs; see `docs/BACKTEST_RESULTS.md`. Independent human sentiment labels, database import, and seller sales records remain outstanding. These are product reviews with genuine customer ratings, not established seller-specific commercial outcomes.

Update: a new Jumia Nigeria review collector is available at `Scraper/jumia_reviews.py`; see `Scraper/README.md` for usage. It retains original dates and ratings, records product provenance, reports weekly coverage, and exports dashboard-compatible import batches. Its tests use constructed HTML/mocked HTTP; inspect live-run reports before claiming a real dataset has been obtained. Your next meeting/deadline is unknown, and some other departments have started submitting. Prioritise a small, complete workflow while confirming your own department's deadline.

## Start here

You already have a software prototype. The next priority is to define what it should predict and obtain data that can test that prediction. You do not need to rebuild the application or train a language model from scratch to take that next step.

Suggested supervisor discussion:

> I have built a prototype that analyses customer review sentiment and forecasts review trends. I propose defining business performance in terms of customer satisfaction and online reputation, using actual customer ratings as a measurable outcome. Is this acceptable for the topic, or do you require sales, orders, or revenue prediction?

If commercial performance is required, obtain actual business outcome records. If a review-based proxy is accepted, state clearly that the system estimates customer satisfaction/reputation rather than financial performance.

## What the existing application does

```text
Customer reviews entered or imported in the dashboard
                       |
                       v
Laravel API: validates and stores the reviews
                       |
                       v
Python API: classifies each review as positive, neutral, or negative
                       |
                       v
Laravel: stores results and groups them into weekly history
                       |
                       v
Python: forecasts sentiment, ratings, and review volume separately
                       |
                       v
Dashboard: displays the review summary, trends, and sentiment outlook
```

| Location | Purpose |
| --- | --- |
| `Frontend/index.html` and `Frontend/src/main.js` | Dashboard, review entry, batch import, and forecast display |
| `Backend/routes/api.php` | Addresses the dashboard calls to retrieve or save information |
| `Backend/app/Services/SentimentService.php` | Connects Laravel to the sentiment API |
| `Backend/app/Services/ForecastService.php` | Builds weekly history and requests forecasts |
| `NLP_Service/model.py` | Routes English/Pidgin text to pretrained sentiment models, with a lexicon fallback |
| `NLP_Service/preprocessing.py` | Cleans review text and recognises Pidgin markers |
| `NLP_Service/forecasting.py` | Forecasts each weekly series using naive/Holt candidates |
| `NLP_Service/evaluation/` | Contains 300 labelled Nigerian Pidgin benchmark examples and an evaluation script |

The production forecast implementation uses each metric's own history. The new offline experiment in `NLP_Service/business_prediction.py` now tests whether earlier sentiment and exchange-rate changes improve future review-volume and customer-rating predictions. Its measured pilot results are documented in `docs/BACKTEST_RESULTS.md`; sales/order prediction still requires actual business outcome records.

## A manageable proposed research question

If your supervisor accepts customer satisfaction as the outcome:

> Does adding previous weeks' customer sentiment improve prediction of next week's average customer rating for a selected Nigerian online business, compared with using rating history alone?

Use one business or a clearly defined case study first. Limit the implemented language scope to English and Nigerian Pidgin, and measure performance for both. These are proposed boundaries to keep the project achievable.

Compare three approaches on the same future weeks:

1. **Simple baseline:** next week's rating equals the last observed weekly rating.
2. **Rating history:** predict using previous ratings only.
3. **Rating history plus sentiment:** add sentiment information available before the prediction date.

The third approach is future work. A simple model is sufficient to begin testing the question; complexity is not evidence of better predictions. A result showing no improvement is still a valid result if the evaluation is sound.

If sales/orders are required, replace the rating outcome with actual weekly sales/orders and make the same comparison. Keep sentiment and outcomes aligned to the same business and dates.

## Data: what you already have and what you need

### Existing demonstration files

`Frontend/samples/sample-batch-balanced-260.json` contains 260 generated records based on five distinct review sentences after removing the `Sample NNN` suffix. Its intended composition is 104 positive-template records, 104 negative-template records, and 52 neutral-template records. It is therefore not evenly balanced across the three classes.

Use these files to demonstrate imports and charts. Repeated sentences with generated dates cannot establish real-world accuracy or forecasting usefulness. The other generated profiles also need correction before they represent mixed distributions: the current positive-heavy and negative-heavy fixtures select only their dominant class templates, and the neutral-heavy fixture selects only neutral templates.

### Existing sentiment benchmark

The 300-item local NaijaSenti sample can support an initial sentiment evaluation. It contains tweets, not business reviews or sales outcomes. Keep its test examples separate from model/rule tuning; use separate development examples when making adjustments. Record which model or fallback produced every prediction.

The Nigerian sentiment model's authors explicitly identify Twitter as its training domain and warn that it may not generalise to other domains. A benchmark score must therefore be supplemented with evaluation on actual business reviews. See the [model card](https://huggingface.co/Davlan/naija-twitter-sentiment-afriberta-large) and [dataset card](https://huggingface.co/datasets/HausaNLP/NaijaSenti-Twitter). Retain dataset attribution and its stated licence when using or redistributing it.

### Business data collection

Use the new collector for a small pilot export, for example 30–50 reviews, to check the fields and import process. This is an engineering check, not a sufficient research dataset or a guarantee that forecasting will be feasible.

Check whether the exported reviews concern a product, a particular seller, or a marketplace service. Do not assign product reviews to a seller unless their provenance supports that association. Keep the product URL/identifier and any verifiable seller identifier in the original export, along with the review date, rating, review identifier, and collection timestamp. Preserve the raw export separately from cleaned/imported data.

Use the pilot to answer four practical questions: are review dates original and parseable; are star ratings available; can duplicate reviews be identified; and can each review be associated with the chosen case study? Then inspect the actual spread of dates and reviews per week before choosing a forecast horizon or expanding collection.

If the script cannot provide suitable records, investigate whether a Nigerian online seller can share existing, anonymised customer reviews with original dates and ratings. An existing historical export is more useful for forecasting than collecting many new reviews on one day. Document the source and how the case study relates to Nigeria.

For each review, retain:

| Field | Why it is needed |
| --- | --- |
| Business identifier | Keeps reviews and outcomes associated with the correct business |
| Original review text | Input to sentiment analysis |
| Original review date | Allows genuine weekly history and chronological evaluation |
| Actual customer star rating, when available | A possible independent satisfaction outcome |
| Source and stable source identifier | Records provenance and helps remove duplicate reviews |
| Language: English, Pidgin, or mixed | Allows analysis of language-specific errors |
| Human sentiment label for an evaluation subset | Provides reference labels independent of the model |

Use an anonymous identifier rather than customer contact details. Have another reader independently label a subset if feasible, and document disagreements and the labelling rules.

Collect both favourable and unfavourable experiences as they occur; do not select only examples that match the expected result. A balanced sentiment test subset and a naturally distributed forecasting history serve different purposes.

Preserve real dates. The dashboard currently enables **Spread undated reviews across 12 weeks** by default: disable that option for research data. A review without its original date cannot establish historical weekly behaviour. Also keep actual star ratings separate from the API's sentiment-derived 1–5 summary score; evaluating one against the other would not provide an independent customer outcome.

The code permits forecasting after eight observed weeks and begins rolling model selection at twelve history entries. These are implementation thresholds, not evidence that the dataset is statistically sufficient. More genuine history and a separate future test period will be needed to assess usefulness; do not fill a shortfall with invented dates.

## Complete the work in this order

1. **Agree the outcome.** Obtain a clear definition of performance and choose a feasible case study. Done when you can name the quantity being predicted, its source, and the prediction horizon.
2. **Establish a reproducible demo.** Run the three application parts, import demonstration reviews, and record one complete review-to-dashboard flow. Done when you can explain each step and show which inference mode is active.
3. **Evaluate sentiment.** Run the existing benchmark evaluation, inspect mistakes, then evaluate a separately labelled business-review subset. Report accuracy, per-class precision/recall/F1, macro-F1, and a confusion matrix. The current script reports accuracy and per-class metrics; macro-F1 and a confusion matrix still need adding.
4. **Test the predictive claim.** With genuine dated outcomes, implement the comparison above. Keep earlier periods for development and later periods for final testing. Predict only with information available at the prediction date. Report MAE/RMSE and whether sentiment improves the baseline.
5. **Write up and demonstrate.** Document the architecture, data provenance, method, results, errors, and limitations. Make dashboard labels match the outcome actually evaluated.

Do not promise an accuracy percentage before measurement. Model confidence is not measured accuracy, and passing software tests does not establish predictive validity.

## Local commands and checks

The commands below assume the project root as the starting directory and the existing environments/dependencies. They do not install anything.

Start the Python service in one terminal:

```bash
cd NLP_Service
../.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Its first startup may download pretrained models. Inspect `http://127.0.0.1:8000/health`: `both_loaded`, `general_only`, `pidgin_only`, and `lexicon_fallback` identify different inference conditions and must be recorded during evaluation.

Use the existing Herd backend at `http://Backend.test`; `Frontend/README.md` describes the dashboard setup. Laravel expects `NLP_SERVICE_URL=http://127.0.0.1:8000`. Check the existing database configuration before running migrations; do not reset an existing database to start the demo.

After starting the Python service, run its existing sentiment benchmark from a second terminal:

```bash
cd NLP_Service
../.venv/bin/python evaluation/evaluate_naijasenti.py
```

It writes an evaluation report under `NLP_Service/evaluation/results/`. The benchmark was not run during this review; no sentiment accuracy result is claimed here.

Software checks run on 29 October 2026:

| Check | Result | Scope |
| --- | --- | --- |
| From `Backend`: `php artisan test` | 19 passed, 77 assertions | Backend unit/feature suite |
| From `NLP_Service`: `../.venv/bin/python -m pytest tests -q` | 31 passed, 3 deprecation warnings | Python tests; API tests deliberately disable live model loading |

These checks do not verify actual model downloads, real model accuracy, the browser workflow, or a connection to the existing business database. Those remain separate verification steps.

## Material for your project report

Adapt this outline to your department's required format:

- **Introduction:** the business problem, aim, objectives, research question, and scope.
- **Literature review:** sentiment analysis, Nigerian English/Pidgin, and prediction of the chosen outcome.
- **Methodology and design:** data collection, annotation, architecture, model choices, chronological evaluation, and baseline comparisons.
- **Implementation and results:** the working application, measured sentiment results, forecast results, and error analysis.
- **Conclusion:** what the evidence supports, limitations, and feasible future improvements.

Your immediate technical task is to run the collector against a current case-study product URL, validate a small real export, and import it into the existing application. In parallel, confirm the actual deadline and proposed performance measure with your department/supervisor. Data inspection and sentiment evaluation can progress while that discussion is pending; the final predictive claim depends on the agreed outcome and available records.
