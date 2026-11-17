# Testing the app

From the project root:

```bash
.venv/bin/python scripts/dev.py
```

Wait for **App ready**, then open [the dashboard](http://127.0.0.1:8080). Click **Use demo account**, then **Sign in**. The local credentials are `demo@pulseboard.test` / `PulseboardDemo!2026`. You can also create an account for your own business. Administrators use [the separate admin page](http://127.0.0.1:8080/admin.html) with their username/password. For the loopback-only local development app, the original `admin` / `admin` works if no stored admin with that username exists.

The launcher runs the frontend on 8080, Laravel on 8001, Python on 8000 and an idle product-tracking worker. The two sentiment models load from their existing local caches. Its default database is `Backend/database/research-demo.sqlite`; your MySQL database is preserved. Ctrl+C stops the services it started; logs are in `.logs/`.

See [Business workspaces](BUSINESS_WORKSPACES.md) for the account/product model, migration safeguards, source tracking and route contracts.

## Test the flow

1. On **Business overview**, confirm 1,733 scored demo reviews across the two products, historical graphs and combined forecasts. Imports belong on product pages.
2. Open **Products**, then Nivea or itel. Nivea has 1,532 scored reviews; itel has 201. Forecasts should appear automatically. Switch between review activity and customer rating, filter reviews and use pagination. Hover the history graph for figures. Click or tap a week, or use arrow keys then Enter, to open its original reviews. Business points include all products; product points keep that product selected. Product/sentiment filters and pagination retain the chosen week. Use the back link to return to the dashboard. Forecast bars show their precise estimates when hovered, tapped or focused. No model choice or backtest action is required.
3. Add a product to a separate registered test business to try review entry/imports without changing the preserved research cases. Import JSON/CSV on that product dashboard. Supply original dates for forecasting; keep demo date assignment off for genuine data.
4. Try reimporting records with stable source IDs: those IDs are deduplicated within the product. If scoring is interrupted, use **Resume scoring** on that product. The browser processes groups of 50 and shows progress. Closing it pauses continuation while saved records remain available.
5. Tracking is off by default. Enable a supported Jumia source only when you want collection. The worker records source failures and retains the last successful snapshot; a blocked website is not treated as a successful scrape.
6. Sign out and register another business. Its dashboard starts empty and the API rejects other businesses' products, review filters and imports.

The original itel `import-001.json` predates stable source IDs and should not be repeatedly imported into the same product. The Nivea import files retain their IDs. Imports do not silently override explicit business/product IDs belonging elsewhere.

## Forecast interpretation

Forecasts concern individual future weekly review counts and average actual customer ratings. The four displayed Mondays begin next week after the chosen cutoff and use direct leads 2–5 from completed history. The current partial week is excluded. The server tunes candidate parameters on past windows and checks a candidate against the incumbent separately for each target/lead. Short histories use simpler estimates. See [Automatic forecasting](AUTOMATIC_FORECASTING.md) for the recorded protocol, learned weights, historical results and promotion gate. The recent error shown in the app is used for model selection; it is not an untouched final test.

The CBN NFEM snapshot has an assumed seven-day lag and no verified real-time publication vintages. Missing economic coverage excludes candidates requiring it. Human sentiment labels and calibrated forecast intervals remain separate work. Revenue, sales, profit and causal economic effects are not inferred.

## Other setups

### Demo login on the configured database (including Herd)

The demo account now has a conventional `Database\Seeders\DemoAccountSeeder`. From `Backend/`, run `php artisan migrate`, then `php artisan db:seed --class=DemoAccountSeeder`. The default `php artisan db:seed` also creates it in local/testing environments. The initial credentials are the same as above. Repeated seeding preserves an existing password, rejects conflicting ownership and does not import or move reviews/products. It works without collected datasets or model caches. Production environments do not receive known demo credentials.

If the demo credentials return 401 at `Backend.test` but work at `127.0.0.1:8001`, check which database each API uses: Herd uses `Backend/.env`, while the normal launcher uses `research-demo.sqlite`. Seed the intended local database or use the launcher's frontend at `127.0.0.1:8080`. The browser address bar sends a GET; authentication requires `POST /api/auth/login` with JSON email/password, or the site's sign-in form.

### Configuration options

- Ports: `--frontend-port`, `--api-port`, `--nlp-port`. Busy ports stop startup without killing another service.
- Configured Laravel database: `--database configured` explicitly runs migrations/seeds against `Backend/.env`. Back up important data first. The normal launcher stays on SQLite.
- Cached Laravel configuration: run `php artisan config:clear` inside `Backend` before demo mode. The launcher stops if a cache could override database isolation.
- Herd: run migrations, the research seeds and the Python service, then the tracking worker using the same environment. Default `Frontend/config.js` targets `http://Backend.test/api`; the launcher serves its own API configuration.
- A fresh checkout needs root `.venv`, Python requirements and Composer dependencies. Model weights and generated evaluation artifacts are ignored by Git. Prepare models using `NLP_Service/scripts/prepare_backtest_model.py` (including the Pidgin repository) and reproduce the itel scoring artifact using the existing [evaluation guide](../NLP_Service/evaluation/business_prediction/README.md).

## Checks

```bash
.venv/bin/python -m pytest NLP_Service/tests Scraper/tests -q
cd Backend
php artisan test
```

PHP tests use an in-memory SQLite database. The optional collector browser tests require their documented opt-in. Tests include date integrity, temporal leakage, missing economic data, resumable 1,000-record imports, account isolation, product-level source-ID deduplication, review-weighted summaries, migration idempotence, and successful/blocked tracking-worker cases.
# Commercial sales and sentiment demo

The [commercial release guide](COMMERCIAL_RELEASE.md) documents the new sales
imports, classification validation, forward check and reproduction. With the
prepared Olist forward files present, the usual local launcher adds a separate
historical demo account: `commerce@pulseboard.test` / `PulseboardDemo!2026` for a
new account. Choose **Use sales research demo**, then **Sign in**. Existing
passwords and other demo ownership are preserved.

Open its portfolio product to inspect sales, forecast ranges, historical errors
and the weekly sales import form. The financial sample ends in August 2018 and
is labelled historical. The Jumia demo receives no invented sales records.
Other accounts need their own complete weekly totals and matching reviews.
