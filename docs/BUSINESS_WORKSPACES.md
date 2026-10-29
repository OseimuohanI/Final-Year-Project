# Business and product workspaces

The application now follows **account → business → products → reviews**. Business summaries combine the underlying reviews; positive percentages and compound scores are not calculated by averaging product averages.

## Try it

```bash
.venv/bin/python scripts/dev.py
```

Open [Pulseboard](http://127.0.0.1:8080). Use **Use demo account**, then **Sign in**, or register your own business account.

Local research demo credentials:

- Email: `demo@pulseboard.test`
- Password: `PulseboardDemo!2026`

The demo is a fictional research workspace grouping the public itel and Nivea product cases. It does not establish that one seller owns or fulfilled both listings.

## Frontend flow

- **Business overview:** totals analysed/saved/pending, positive sentiment, average compound score, actual customer stars, historical graphs, automatic combined feedback forecasts, and product comparison cards. There are no review import forms here.
- **Products:** catalogue of the business's products, with Add product and product-level metrics.
- **Product dashboard:** the same metrics and historical/forecast graphs scoped to one product, review entry, JSON/CSV batch imports, resumable scoring, paginated/filterable reviews and tracking controls.
- **Authentication:** registration creates a business and its first user. Login establishes a 12-hour bearer-token session. Only the token hash is stored server-side. Logout revokes the current token and clears the frontend session/drafts.

Imports require a product. Files without business/product IDs are assigned to the currently open product. Files explicitly naming another business/product are rejected rather than silently reassigned. Stable source-review IDs are unique within a product, so the same native ID may legitimately exist on two products. Imports still run in groups of 50 and retain progress across failures.

## Data ownership

The API protects every business, product, review, forecast, import, scoring and tracking route. A user can only access the business referenced by their account. Product and review filters are checked before queries or writes. Mixed batches containing another business's product are rejected before saving anything. Administrator routes are separately protected with admin tokens; business tokens cannot access administration, and admin tokens do not act as business-owner sessions.

| Resource | Owner / scope |
| --- | --- |
| `users` | Business membership |
| `business_tokens` | User, hashed token, expiry |
| `products` | Business |
| `reviews` | Product and matching business |
| `sentiment_results` | One result per review |
| `saved_outlook` | Separate JSON result on the business or product |

The first release has account creation/login/logout and one owning business per account. Password recovery, email verification and staff invitations remain future account-management work.

## Preserved research data

Before restructuring, a complete SQLite backup and review/sentiment snapshot were saved locally:

- `.logs/backups/before-business-products.sqlite`
- `.logs/backups/before-business-products.json`

`php artisan research:prepare-workspace` moves the recognised legacy public cases into product records in the demo business. It is idempotent and does not create duplicate review or sentiment records. The original business rows are archived after their reviews move; `products.legacy_business_id` retains the link. Existing saved product-case outlooks are copied into the corresponding product. The old business forecast rows remain attached to archived records for provenance, not presented as combined-business forecasts.

The 201 itel reviews and 1,532 Nivea reviews retain their original review IDs, texts, dates, stars, source IDs and sentiment rows. Four older verification reviews remain preserved outside the demo workspace. Unknown legacy businesses/accounts are not automatically assigned to a new user.

The seed runs only in local/testing environments. It does not overwrite an existing user's password or take over a demo email belonging to another business. The optional `--collections-root` argument supports isolated migration fixtures.

Structural migrations and a data move are distinct operations. Restore a backup to reverse the data move; do not assume a schema rollback restores the former business/product assignments. The normal launcher uses the separate SQLite database. MySQL remains unchanged unless you explicitly launch with `--database configured`.

## Product tracking worker

The local launcher starts a fourth service, alongside the frontend, Laravel and Python APIs:

```bash
# Standalone worker, using the same database/NLP environment as the API:
php artisan products:track --watch --sleep=30

# One pass over currently due products:
php artisan products:track
```

Products start with tracking **off**. On a product dashboard, enter an HTTPS Jumia Nigeria product/review URL, enable tracking, choose the interval and save. The worker checks due products. **Check now** schedules an immediate check; it does not hold a browser request open during collection.

The worker claims one due product atomically, runs the existing identified collector, retains its source artifacts, imports only that product's new source IDs, scores pending reviews in bounded groups, and refreshes an existing product forecast when scoring completes. The original collection rules, request delay, access-block handling and page/review limits apply. Successful collection metadata updates the product's coverage/cutoff. Failed access leaves the last successful snapshot intact, records an error and schedules the next attempt. It does not bypass source challenges or invent reviews. Tracking errors and last/next check times are shown on the product dashboard. While tracking is enabled, the frontend polls a tenant-scoped activity fingerprint every 30 seconds and refreshes changed views, preserving form drafts and scroll position.

Only Jumia Nigeria is supported by the current connector. Additional websites require their own collectors. Live availability still depends on the source accepting requests; offline tests verify both successful ingestion and access-denied behaviour. No external collection is started just by opening the demo.

## Forecast scope

Business and product outlooks use the same tested Python models with different review queries and separate saved results. Business collection coverage/cutoff is derived from products with reviews, using the earliest known collection cutoff where all are known. Future periods exclude the unfinished current week. Review activity and actual customer ratings remain the targets; neither becomes sales or profit by being combined across products.

Forecasts are now selected and fitted automatically. The server uses the collection cutoff/coverage, compares candidates on chronological history, and retains the incumbent unless a candidate passes the promotion check. Customers see estimates and historical error without running evaluations. Selection error is not independent final accuracy. See [Automatic forecasting](AUTOMATIC_FORECASTING.md) for the current policy; explicit research models remain available through the API for reproducibility.

## Routes

Public: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/status`.

Authenticated:

- `GET /api/auth/me`, `POST /api/auth/logout`
- `GET /api/businesses`, `GET /api/businesses/{id}`, `GET /api/businesses/{id}/trend`, `GET /api/businesses/{id}/activity`
- `GET /api/businesses/{id}/outlook`, `POST /api/businesses/{id}/outlook/generate`
- `GET/POST /api/products`, `GET/PATCH /api/products/{id}`
- `POST /api/products/{id}/outlook/generate`
- `GET /api/products/{id}/reviews/scoring`, `POST /api/products/{id}/reviews/score-pending`
- `POST /api/products/{id}/tracking/check`
- `GET/POST /api/reviews`, `POST /api/reviews/batch`

The older univariate business forecast routes remain authenticated for compatibility. The main UI uses the scoped research outlooks.

## Administrator sign-in

Open [the admin page](http://127.0.0.1:8080/admin.html), or choose **Administrator sign-in** on the business login screen. Stored administrators keep their existing usernames/passwords. The old `admin` / `admin` demo login is supported only when `APP_ENV=local`, the request originates from loopback, and there is no stored administrator named `admin`. It never bypasses an existing password. Local-demo tokens are rejected outside that environment and origin.

The separate admin workspace lists businesses, product/review/owner counts and archived status, and restores business-record creation. Creating a business record does not create owner credentials or attach an existing owner's account; owner registration remains in the business app. Admin tokens use their own frontend storage, hashes and 12-hour expiry. Sign-out revokes the active token. No stored administrator credentials are changed by this fix.

Admin API: `POST /api/admin/auth/login` (rate limited); protected `GET /api/admin/auth/me`, `POST /api/admin/auth/logout`, `GET/POST /api/admin/businesses`, and the restored `POST /api/admin/auth/admins`.
