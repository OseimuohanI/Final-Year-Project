# Application verification — 29 October 2026

The running application was verified with the actual Python service, Laravel API and frontend, using the separate SQLite research database. The original MySQL database was not migrated or changed.

- Automated checks: **101 Python tests passed**, two optional collector browser integration tests skipped; **28 Laravel tests passed** (126 assertions). PHP formatting and Git whitespace checks passed.
- Both cached sentiment models loaded. Live review scoring exercised the general route and a recognised Pidgin marker route. Pidgin phrasing without a curated marker also exercised the existing general-route limitation, documented in the testing guide.
- The original 201-review itel case remains unchanged. The app uses 193 reviews in 36 completed calendar weeks; eight current-week reviews are excluded and two empty weeks retain an explicit complete-collection assumption.
- Model switching generated real results with sentiment alone and sentiment plus CBN exchange rates. Review/rating tabs and backtest lead selection worked. Lead-four errors match the earlier pilot to the displayed precision.
- Future weeks begin 2, 9, 16 and 23 November 2026. All eight projected target points and 384 per-model backtest predictions were checked through the live API. Training outcome cutoffs passed temporal assertions; these predictions are not 384 independent test weeks.
- Quoted CSV text was preserved. Reimporting stable IDs skipped both duplicates. A deliberately generated demo date was excluded from research history. The separate sandbox business correctly displayed insufficient-history messages; adding a later record marked its saved result stale.
- The research seeder was run twice and still contains exactly 201 case reviews.
- Desktop at 1280px displayed two result columns; phone at 390px displayed one, with no document overflow. Target switching worked on both. The final browser console contained no errors.

Detailed live checks are in `../.logs/app-verification.json`. Screenshots are in `../.logs/screenshots/`. The model weights, test database, service logs and screenshots are local workspace artifacts rather than source-controlled files.

Start and use the app with [the testing guide](TESTING_THE_APP.md). Forecasts concern public feedback activity and ratings. Sales records, independent sentiment labels and calibrated forecast intervals remain future work.

## Large-import follow-up

A subsequent real 1,000-record import exposed PHP's 30-second execution limit: reviews were saved before inference, but the original all-at-once response never stored their scores. The resulting fatal 500 omitted normal CORS headers. This path is now bounded to 50 scoring records per request, with persisted progress and Resume scoring. The frontend sends sequential groups of 50, and only requests optional forecast/outlook resources when business detail says they exist.

The actual 1,000 pending Nivea reviews were recovered through the dashboard, then the second file's 532 reviews were imported and scored. Reimporting the first 1,000 records skipped every duplicate and added no records. All 1,532 source IDs, texts, original dates and stars match the preserved collection, every review has a sentiment result, and the original 201-review itel case is unchanged. The later Laravel suite passed 32 tests, including the full 1,000-record API payload, business-scoped recovery, bounded timeouts, JSON/CORS error responses and progress preservation across a simulated service failure. Details are in `.logs/import-recovery-verification.json`.

## Business and product workspace verification

The account-based business flow was exercised through the running browser and API. The latest automated suite passed **45 Laravel tests (338 assertions)** and **103 Python tests**, with two optional collector browser tests skipped. PHP formatting and whitespace checks passed.

- Registered a separate business, created a product and imported two quoted CSV reviews through its product dashboard. Its overview displays only those two reviews. The research demo displays 1,733 scored reviews across its two products, with no import controls on the business overview.
- Verified unauthenticated requests return 401 and another business cannot read, import into, filter by, or score the demo products. Logging out revokes the bearer token.
- Reimported the 1,000-record Nivea batch: zero added, all 1,000 duplicates skipped. All 1,737 original reviews retain their IDs, source IDs, text, original dates, stars and sentiment results; only the intended business/product assignments changed. A pre-migration database backup is retained locally.
- Business and product outlooks use their own histories. Switching pages during a forecast request does not replace the destination page's result. The forward model now uses the same eligible economic-history policy as its rolling comparison; older saved model revisions are marked stale.
- The tracking worker's successful, disabled and blocked-source paths passed fixture tests. A failed collection preserves the previous successful coverage snapshot. No live collection was triggered for this verification; research tracking remains disabled. The dashboard polls a scoped activity fingerprint every 30 seconds when tracking is enabled.
- Desktop (1280px) and phone (390px) layouts were checked without document overflow. Product drafts survive chart changes. Review filtering and pagination were exercised in the browser.

The structured preservation and isolation checks are in `.logs/business-workspace-verification.json`. Screenshots include `.logs/screenshots/business-overview.png`, `.logs/screenshots/product-catalogue.png`, and `.logs/screenshots/product-mobile.png`. See [the business workspace guide](BUSINESS_WORKSPACES.md) for the migration and monitoring behavior.

## Admin login restoration

Restored the administrator routes and added a separate admin sign-in/management page after the business account migration removed the old entry point. Stored administrator credentials are unchanged. The legacy default login is restricted to loopback in the local environment and cannot override a stored administrator password. Admin and business tokens are not interchangeable. Tests cover stored-admin login, business listing/creation, admin creation, token revocation/expiry, local-demo origin/environment restrictions, orphaned tokens and account-type separation. The updated Laravel suite passed 51 tests. Live browser verification exercised the local admin login, session restoration and logout. The resulting management view is saved in `.logs/screenshots/admin-management.png`.

## Automatic forecasting release

The updated suite passed **56 Laravel tests (394 assertions)** and **114 Python tests**, with two optional collector browser tests skipped. PHP formatting and whitespace checks passed. The eleven new Python forecasting tests include future-outcome invariance, chronological fitting/selection cutoffs, learned-weight behavior, target separation, missing inputs, short-history handling, the promotion gate and compact public diagnostics. Five new Laravel tests cover automatic business/product generation, caching, review/coverage invalidation, preserving a saved result on service failure and rejecting browser-supplied coverage/cutoff overrides.

The live API produced automatic results for the 1,733-review business, the 1,532-review Nivea product and the 201-review itel product without model/evaluation options. Repeated unchanged calls returned the same saved generation; the warm itel request took about 24ms. All 1,739 existing review and sentiment records were unchanged. Structured checks are in `.logs/automatic-forecast-verification.json`.

The browser showed automatic forecasts on arrival, separate product and business histories, working review/rating switching and refresh, no backtest text or model picker, no console errors, and no document overflow at 390px or the normal viewport. The temporary phone viewport was reset. Screenshots are `.logs/screenshots/automatic-business-forecast.png` and `.logs/screenshots/automatic-forecast-mobile.png`.

See [the release report](AUTOMATIC_FORECASTING.md) for all six target comparisons and the explicit limitation: historical promotion results are model-selection evidence, not an independent final test. The initial challenger results remain unchanged after the promotion gate was added; failed candidates were not retuned against the outer block.

## Graph inspection

Added weekly chart tooltips with a crosshair and point marker for review activity, sentiment and customer ratings. The tooltip includes the week, formatted value/unit and partial-week context. Unknown values keep their missing-data label and have no point marker. Forecast bars are focusable and show precise estimates identified as forecasts. Values are inserted with textContent.

Browser checks covered counts, sentiment (four decimals), ratings, Home/End and arrow navigation, an empty historical week, forecast inspection, Escape dismissal, and a 390px layout without tooltip/document overflow. The normal viewport was restored. Screenshot: `.logs/screenshots/chart-weekly-tooltip.png`. This is a frontend display change; no forecasting or source-data changes were made.

## Safari cached-style correction

Reproduced the reported tooltip problem in the user's Safari app: the new JavaScript was running, but the graph used the older stylesheet, leaving the tooltip as inline text and the graph at intrinsic SVG width. A normal Safari reload restored the floating tooltip and full-width graph without changing chart code. Verified Safari review counts, sentiment values, rating selection, keyboard navigation and the forecast tooltip.

Both HTML entry pages now use content-hashed local CSS/JS URLs. `Frontend/scripts/version_assets.py` regenerates them, and the launcher runs it at startup. Manual checks confirmed idempotence, a changed stylesheet getting a changed URL, and preservation of external/parent paths. Existing sessions/data are unaffected. The saved native Safari proof is `.logs/screenshots/safari-chart-tooltip.png`.

## Chart-to-review navigation

Historical points now open a dedicated weekly review view. Safari mouse click-through was verified on the Nivea sentiment graph: the selected week, product and original scored reviews were retained. Business keyboard navigation (arrows then Enter) opened the 18–24 May 2026 dip, whose 28 reviews and average compound score 0.4842 match the graph. Lowest sentiment scores appear first, with actual product names, original text/stars and compound scores. Product links keep the same week; sentiment/product filters reset pagination while retaining that period. Reload preserved the selected product, week and negative filter. Pagination retained the full-period summary.

The suite passed **61 Laravel tests (438 assertions)**, including five new tests covering Lagos week boundaries, exact agreement with the historical aggregate, pending sentiment/actual ratings, estimated/undated exclusions, product and sentiment filtering, pagination, invalid input, empty periods and account isolation. Browser checks confirmed no document overflow at 390px; the viewport was reset. Screenshot: `.logs/screenshots/weekly-review-drilldown.png`.

## Reference dashboard design revision

Reworked the interface around the supplied dashboard reference: a pale blue-grey canvas, white utility bar and sidebar, flat white panels, light Roboto headings and figures, rectangular controls and blue/green/violet chart accents. The shared appearance layer also covers product pages, weekly reviews, forms and the admin interface. New sessions start in light appearance; an explicit saved dark preference is respected.

Live browser checks at the reference's 1503px width and at 390px confirmed responsive layouts without document overflow. The desktop sidebar toggle, mobile drawer, add-product dialog, chart figures and keyboard navigation into the correct weekly reviews worked. Native Safari reloaded the revised layout successfully. Asset URLs remain content-hashed. Screenshot: `.logs/screenshots/reference-dashboard.png`. This revision changes presentation only; forecasting models and review records were not modified.
