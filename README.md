# Pulseboard — Nigerian online business sentiment analysis

A research prototype with a review dashboard, Laravel API, English/Pidgin sentiment service, and Jumia review collector.

For the final report, see the [development account and report-writing guide](docs/REPORT_DEVELOPMENT_ACCOUNT.md). It explains what was implemented, why the main choices were made, the measured results and their limits, and the supporting evidence.

## Repository setup

This parent repository pins the Backend, Frontend and NLP_Service repositories as Git submodules. The scraper, shared documentation and launcher are maintained directly here.

```sh
git clone --recurse-submodules git@github.com:OseimuohanI/Final-Year-Project.git
cd Final-Year-Project
```

For an existing clone, run `git pull --ff-only`, then `git submodule sync --recursive` and `git submodule update --init --recursive`. The NLP submodule now lives at `NLP_Service/`, matching the application scripts; older parent revisions used `PythonNLP/`. Preserve any local work in the old folder before updating an older checkout.

See [repository maintenance](docs/REPOSITORIES.md) for component URLs and the commit/push order.

A new clone does not contain local environments, credentials, databases, model weights, collected reviews or generated evaluation results. The research demo launcher requires the preserved itel collection and scoring artifacts; restore/reproduce those and install dependencies as described in [the testing guide](docs/TESTING_THE_APP.md) before starting it. The 1,733-review demo describes this workspace's data, not data bundled into Git.

## Try the complete application

```bash
.venv/bin/python scripts/dev.py
```

Open [Pulseboard](http://127.0.0.1:8080), use **Use demo account → Sign in**, then explore **Business overview → Products → Product dashboard**. The demo login is `demo@pulseboard.test` / `PulseboardDemo!2026`. Forecasts appear automatically, with model fitting and evaluation handled internally. See the [forecasting release report](docs/AUTOMATIC_FORECASTING.md). Business metrics aggregate product reviews; imports, resumable scoring and tracking live on product dashboards. The launcher uses separate SQLite data and starts a product-tracking worker. See [the testing guide](docs/TESTING_THE_APP.md) and [workspace design](docs/BUSINESS_WORKSPACES.md).

## Start the review collector

From this project folder:

```bash
.venv/bin/python Scraper/jumia_reviews.py
```

Paste a Jumia Nigeria product URL when prompted. Browser mode watches document/review responses, selects the HTML containing reviews, follows the full-review and next-page links, and saves a collection under `Scraper/data/collections/`. The contact previously supplied for this project is in the ignored `Scraper/.env` file.

See [collector setup and usage](Scraper/README.md), including browser installation, direct HTTP mode, and saved-page processing.

## Where things belong

| Folder | Contents |
| --- | --- |
| `Frontend/` | Dashboard entry page and source files |
| `Frontend/samples/` | Original synthetic review import fixtures |
| `Frontend/scripts/` | Fixture generation utilities |
| `Backend/` | Laravel API, database migrations, and PHP tests |
| `Backend/scripts/` | Backend maintenance utilities |
| `NLP_Service/` | Python API, sentiment model, preprocessing, aggregation, forecasting |
| `NLP_Service/tests/` | Automated Python service tests |
| `NLP_Service/evaluation/` | Benchmark data and evaluation scripts |
| `NLP_Service/examples/` | Manual example API payloads |
| `NLP_Service/experiments/` | Original exploratory forecasting diagnostics |
| `Scraper/` | Collector code, dependency list, and tests |
| `Scraper/data/collections/` | Collected datasets, imports, reports, and source captures |
| `Scraper/data/archive/` | Failed pilots and old verification output |
| `docs/` | Project guide and file-move record |

The frontend, backend, and Python service retain their existing Git repositories. Local environments and IDE settings remain in place.

## First real dataset

The [itel IESS-320T collection](Scraper/data/collections/itel-power-station/DATASET_NOTES.md) contains 201 deduplicated product reviews with original dates and customer ratings. Its [import file](Scraper/data/collections/itel-power-station/import-001.json) is ready for the existing dashboard. Select the intended case-study business, disable artificial date spreading, and import once.

The reviews have now been scored with a pinned pretrained sentiment model and used in a retrospective forecasting pilot. Independent human sentiment labels and seller sales records remain unavailable.

The [prediction design proposal](docs/PREDICTION_DESIGN.md) explains how customer sentiment and Nigerian economic indicators could be tested together, which public sources are available, and which claims require actual business outcome records.

The [completed backtest results](docs/BACKTEST_RESULTS.md) compare the existing forecaster, simple baselines, and models using sentiment/CBN exchange rates on the real review history. See the [evaluation instructions](NLP_Service/evaluation/business_prediction/README.md) to reproduce the offline experiment.

## Second real dataset

The [Nivea Dry Impact collection](Scraper/data/collections/nivea-dry-impact/DATASET_NOTES.md) contains **1,532 unique review fingerprints** collected from all 155 review pages, dated **26 April 2022–27 October 2026**. It provides 235 completed calendar weeks at the collection cutoff. The two numbered import files contain 1,000 and 532 dated records. It is imported and sentiment-scored in its own product record within the research demo workspace. Both product and combined-business outlooks are available; the original itel pilot remains a separately documented experiment. Large imports now support progress and resumable scoring; see the [testing guide](docs/TESTING_THE_APP.md).

## Run the application and checks

See the [frontend instructions](Frontend/README.md), [backend instructions](Backend/README.md), and [project guide](docs/PROJECT_GUIDE.md). Start the Python service from the project root with:

```bash
.venv/bin/python -m uvicorn main:app --app-dir NLP_Service --host 127.0.0.1 --port 8000
```

Run Python tests:

```bash
.venv/bin/python -m pytest NLP_Service/tests Scraper/tests -q
```

Run backend tests from `Backend/` using `php artisan test`.

The [file-move record](docs/FILE_MOVES.json) maps scattered files to their new locations. No research data or exploratory scripts were deleted during reorganisation.
