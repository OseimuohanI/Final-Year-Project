# Development account and report-writing guide

Project: **Design and Implementation of a Sentiment Analysis System to Predict the Performance of an Online Business in Nigeria**

Prepared from the conversation, the current implementation and retained project evidence. The collected-data and evaluation snapshot is **29 October 2026**. This is material for drafting the final report, not a claim of supervisor approval, a literature review, or a substitute for independent research evaluation.

## 1. What was accomplished and how to describe it

The project was developed from an existing sentiment-analysis prototype into an integrated application, named Pulseboard, that collects or imports product reviews, analyses their sentiment, organises them by business and product, displays historical customer-feedback metrics and automatically produces four future weekly estimates of review activity and customer ratings.

The work in this conversation included defining a measurable prediction scope, implementing and refining a Jumia review collector, obtaining two real dated review datasets, building a retrospective forecasting experiment with Nigerian exchange-rate data, integrating forecasting into the application, fixing large imports, implementing business/product accounts and monitoring, restoring administrator access, automating forecast selection, adding chart inspection and review navigation, resolving a Safari asset-cache problem and revising the interface using the supplied visual reference.

There were already frontend, Laravel and Python service repositories, pretrained sentiment inference, generated import examples and an earlier time-series forecasting module when this conversation started. The report should describe this as development and extension of that prototype. It should not imply that the pretrained language models, their pretraining datasets or every pre-existing module were created during this conversation.

The strongest supported description of the completed prediction task is:

> The system uses historical product-review activity, text-derived customer sentiment and, where available and selected, lagged Nigerian exchange-rate information to estimate future weekly public-review activity and actual customer star ratings. It provides separate product and business-level views and performs chronological forecast selection internally.

The current outcomes are **public-feedback performance indicators**. The system has not been validated to predict sales, orders, revenue, profit, market share or the probability that a business will succeed. No seller transaction dataset has been supplied. The chosen interpretation of “business performance” still needs to be accepted by the supervisor if the original topic is retained.

## 2. The initial problem and the scope decision

At the beginning, the supervisor had not specified how performance should be measured and no business records had been collected. The existing generated reviews could demonstrate the interface but could not establish real-world accuracy. The user proposed adding publicly available country, economic and sector data to forecast the direction of a business.

That idea was converted into a testable question:

> Does earlier customer sentiment add predictive information about future review activity or customer ratings, compared with a forecast using outcome history alone? Does exchange-rate information add anything further?

Two observable outcomes were selected:

| Outcome | Meaning | Unit | What it does not establish |
| --- | --- | --- | --- |
| Weekly published written-review count | Public feedback activity for the selected listing | Reviews per week | Sales, orders, demand or profit |
| Future weekly average actual star rating | Satisfaction expressed by customers who left rated written reviews | Stars, 1–5 | Satisfaction of every buyer or the performance of every seller |

These outcomes were chosen because the supplied Jumia pages contained dates, review text and genuine customer stars that could be retained and checked. A single self-defined “business success” score would have lacked an independent outcome against which to validate it. National economic statistics could be predictors, but could not replace missing seller outcomes.

Weekly aggregation was a practical compromise: daily product reviews were sparse, while monthly aggregation would leave very few observations in the short itel case. This is a methodological justification, not evidence from a controlled daily-versus-weekly model comparison. The weekly frequency and four-week display horizon are prototype design choices rather than proven optimal settings.

## 3. System architecture and technology choices

The implementation maintains four main components and a development launcher:

| Component | Actual implementation | Responsibility and reason for retaining it |
| --- | --- | --- |
| Frontend | HTML, CSS and vanilla JavaScript | Account screens, dashboard, product pages, imports, charts, review inspection and tracking controls. Extending the existing frontend avoided an unnecessary framework migration and an npm build dependency. |
| Application backend | Laravel/PHP | Authentication, ownership checks, validation, persistence, data aggregation, imports, forecasting requests and tracking coordination. It remained the authority for business data. |
| NLP and forecasting service | Python/FastAPI, Pydantic, Transformers/PyTorch and numerical libraries | Sentiment inference and forecasting. Python already hosted the models and research code, so this boundary kept model work independently testable. |
| Review collector | Python, Beautiful Soup, HTTP client and Playwright browser mode | Source acquisition, response selection, parsing, pagination, deduplication and provenance exports. |
| Local launcher | `scripts/dev.py` | Starts the frontend, Laravel API, Python service and tracking worker with a consistent local configuration. |

The browser communicates with Laravel. Laravel stores reviews and calls the Python service; the browser does not fit models or supply trusted collection metadata. The collector exports source records and import files; the tracking worker can also invoke it and ingest new records.

The local demonstration uses a separate SQLite database. The previously configured MySQL database was not silently migrated or replaced. This allowed the application to be tested without altering the user's original database. SQLite here is a development and research convenience; this work did not establish production-scale database performance.

This separation supports reproducibility and independent tests. It also introduces operational requirements: all services must use matching API addresses, contracts and data formats. The launcher, health checks, configuration and error messages were added/refined to make that manageable.

## 4. Review collection: what was built and why

### 4.1 Interactive, response-aware collection

`Scraper/jumia_reviews.py` can ask for a Jumia Nigeria product URL instead of requiring source-code edits for each product. It supports browser response capture, direct HTTP requests and offline processing of saved HTML.

The requested response-targeting behaviour was implemented by observing browser document responses and review-related XHR/fetch responses, then selecting successful HTML containing review cards, a full-review link or an explicit zero-review state. It also recognises HTML fragments nested in JSON responses. It does not assume that Jumia exposes a separate public JSON review API, and it does not reinterpret arbitrary JSON arrays as reviews.

The collector follows the actual full-review and Next Page links. This was chosen over guessing page endpoints because the links provide evidence of the source's real navigation structure. Full-review responses take precedence over the small review preview on the product page.

### 4.2 Why multiple acquisition paths were necessary

Direct HTTP requests to the supplied itel product and its review URL returned HTTP 410. A newly launched local Chromium collector session also encountered 410. The in-app browser could display the review pages without a challenge, so the real datasets were obtained through browser-assisted capture of review DOM excerpts and then processed with the same Python parser.

Consequently, these are **real browser-assisted collections**, not evidence that a direct HTTP scraper successfully retrieved those datasets. Saved DOM excerpts are also not full original HTTP response bodies. Offline replay reproduced the processed data and made parser verification possible without repeatedly requesting the source.

The response-capture collector has automated and optional real-browser fixture tests. Fixture success verifies its behaviour under those conditions; it does not guarantee that Jumia will accept every live collector session. Automatic collection remains dependent on source availability.

### 4.3 Fields and provenance

The collection pipeline preserves the review title/body, original date, actual customer stars, product URL/SKU, source URL, collection time and an identifier or content fingerprint. It writes raw processed records, dashboard import batches, collection/coverage reports and source captures/manifests. The larger Nivea case also has replay checks and checksums.

Native IDs are used where available. Otherwise the fingerprint uses product information and review content/date/rating/byline. This removes repeated source entries but cannot prove that each retained fingerprint belongs to a different human customer. The report should say “unique review fingerprints” or “deduplicated review records,” not “verified unique customers.”

Source excerpts retain public bylines where needed for reproduction. Processed records do not include a separate reviewer-name field. The configured collector contact is held in ignored local configuration and identifies live collector requests; it is not a modelling feature.

Original dates and stars were kept because generating dates would create a fictional timeline, and converting sentiment into stars would contaminate an independently observed outcome. Missing/invalid source values are reported as exclusions rather than silently fabricated.

### 4.4 Collection controls

The live collector reads crawler instructions, identifies its contact, uses at least a three-second content-request delay, applies page/review limits and stops on access failures such as 401, 403, 410 or 429. Limits, partial results and failures are reported. Existing output directories are not overwritten. These choices make collection bounded and auditable; they do not establish ownership of the source data or guarantee access.

The standard CLI limits are 30 navigations and 1,000 unique valid records, configurable up to 500 navigations and 10,000 records. The Nivea replay overrides the defaults because it covers 155 review pages. Product tracking uses the higher bounded limits.

## 5. The actual datasets

The following counts refer to the preserved 29 October 2026 collection snapshot:

| Property | itel IESS-320T power station | Nivea Dry Impact roll-on, pack of 3 |
| --- | ---: | ---: |
| Review-listing pages traversed | 21 | 155 |
| Written entries in those listing pages | 205 | 1,545 |
| Deduplicated review fingerprints | 201 | 1,532 |
| Original review dates | 17 February–28 October 2026 | 26 April 2022–27 October 2026 |
| Completed calendar weeks at cutoff | 36 | 235 |
| Reviews in completed weeks | 193 | 1,529 |
| Current partial-week reviews excluded from forecasts | 8 | 3 |
| Completed weeks without a visible review | 2 | 24 |

The itel collection spans 37 calendar weeks including the unfinished final week; 35 have reviews. It is roughly nine calendar months, not a full year. The Nivea collection spans 236 calendar weeks including the final partial week, with 212 observed weeks. It provides a much longer second product history, about four and a half years, although many weeks are sparse.

The Nivea product displayed 10,227 aggregate ratings, but only 1,545 written-review entries. The 1,532 retained text-review records must not be described as all those aggregate ratings. Ratings without review text were not converted into invented review records.

Both datasets are heavily skewed toward high stars:

| Customer stars | itel | Nivea |
| --- | ---: | ---: |
| 1 | 2 | 28 |
| 2 | 3 | 23 |
| 3 | 9 | 64 |
| 4 | 28 | 261 |
| 5 | 159 | 1,156 |

The research demo contains both products and therefore 1,733 reviews. It is a **fictional combined workspace** for demonstrating business aggregation. The source evidence does not establish that the same real seller owned or fulfilled both listings. A result for this workspace must not be presented as independent validation on a real two-product seller.

The system imported and scored all 1,733 research reviews. Source/import files remained separate from database predictions. The initial itel collection note and some older guides still contain historical statements such as “not imported” or “no import deduplication”; later implementation and verification supersede those statements. Use the current workspace and automatic forecasting documentation for present behaviour.

### Synthetic data and benchmark data are different

The earlier 260-record “balanced” fixture is generated demonstration data, based on only five distinct sentences once sample suffixes are removed. Its intended 104 positive, 104 negative and 52 neutral records are not equally balanced across three classes. These files were retained for imports/UI tests, not used as evidence of real forecasting accuracy. Other fixture profile names also should not be treated as verified empirical class distributions.

The repository also contains a 300-item NaijaSenti Nigerian Pidgin test sample and evaluation tooling. It is tweet-domain benchmark material, not Jumia business reviews, training data for the new forecaster or sales records. No new measured business-review sentiment accuracy is established by merely including that benchmark. Its source attribution and stated licence must be retained when it is used or redistributed.

## 6. Sentiment analysis: what the application actually computes

The project uses pretrained classifiers. The configured general model is `cardiffnlp/twitter-xlm-roberta-base-sentiment`; the Nigerian Pidgin-oriented model is `Davlan/naija-twitter-sentiment-afriberta-large`.

The router checks for one or more curated Pidgin markers using phrase boundaries. Marked text goes to the Pidgin classifier; other text goes to the general classifier. One preferred classifier is called per review. If it is unavailable, the other loaded classifier is used; if neither is available, an explicitly identified English/Pidgin lexicon fallback is used. This is routing, **not an ensemble average of two language-model outputs**, and it is not a comprehensive language-identification system.

Preprocessing handles HTML entities/tags, URLs and mentions, hashtag text, whitespace, Unicode and curly quotes, repeated characters/punctuation and selected sentiment-bearing emojis. The original source text remains stored separately. This aims to reduce input noise while keeping useful linguistic content; no new ablation study proves that each cleaning operation increases accuracy.

Each scored review stores:

- `label`: positive, neutral or negative;
- `confidence`: the winning classifier score;
- `compound_score`: a signed score in the range −1 to +1;
- `model_used`: general, pidgin or lexicon_fallback.

For a transformer prediction, compound score is **+confidence for positive, −confidence for negative and 0 for neutral**. It is not VADER's compound score, a calibrated probability of satisfaction or the difference between positive and negative probabilities. The fallback uses its own bounded lexicon score, so model provenance matters when interpreting mixed outputs.

The dashboard calculates positive share as positive predictions divided by all scored reviews. Average compound score is the mean of available scored reviews. Customer rating is calculated from original customer stars independently, including where text scoring is pending.

This separation avoids a circular result in which model-produced sentiment is treated as both an input and a supposedly independent star-rating target. A high star rating can coexist with negative text, and the system preserves that disagreement.

The initial itel forecasting experiment pinned the general model to revision `f2f1202b1bdeb07342385c3f807f9c07cd8f5cf8` and recorded scoring/code hashes. Its existing marker detector found no marked itel reviews. Nivea's detector matched one review, which is not a reliable estimate of all Pidgin text in that corpus.

The language models were **not fine-tuned on these collections**. There are no independent human reference sentiment labels for them. We therefore cannot report a new Jumia sentiment accuracy/F1 or claim the forecasting work made the sentiment classifier more accurate. Twitter-trained model transfer to product reviews, short comments, mixed languages, slang, negation and sarcasm remain limitations.

## 7. Weekly history and data-quality rules

Calendar weeks are Monday-based in **Africa/Lagos**. Weekly review navigation converts the local period to the appropriate UTC query boundaries. Using one definition throughout prevents the chart and its review list from disagreeing at week boundaries.

For each week the forecasting input retains review count, rating sum/count, sentiment sum/count and whether reviews were observed. Sums and denominators permit genuine pooled averages rather than averages of unequal-sized groups.

The rules are:

1. Use original dated records for historical forecasting.
2. Exclude undated records and dates marked as demo-estimated.
3. Exclude outcomes from the current incomplete week.
4. Do not extend an old collection beyond its known collection cutoff with imaginary empty weeks.
5. Treat an absent week as zero reviews only under an explicit complete-collection assumption. Otherwise count remains unknown.
6. Leave sentiment and rating missing when there is no corresponding observation. A zero-review week does not have a neutral rating or neutral sentiment.
7. Count all eligible dated reviews for activity, actual stars for ratings and available scores for sentiment. Pending inference must not delete genuine review activity or star evidence.

“Complete” means complete for the visible paginated review listing at capture time. It does not prove that a presently absent historical review never existed. Historical deletion, moderation, publication delays and changing participation remain possible sources of bias.

The itel weekly sample has 36 completed calendar weeks, not 201 independent time-series examples. Lags, missing outcomes and forecast horizons reduce the eligible regression sample further. Likewise, repeating a monthly economic observation across several weeks would not create independent monthly information.

At business level, metrics are recomputed from the underlying reviews. For example, one product with 100 scored reviews at 90% positive and another with 10 at 50% positive yields 95/110 = 86.36% positive, not the unweighted average of 70%. The same principle applies to pooled sentiment and stars. This preserves the interpretation “across reviews”; it does not estimate a sales-weighted product portfolio.

## 8. Nigerian economic context: implemented and deferred inputs

Exchange rates, inflation/CPI, petrol prices, sector/business surveys and electricity statistics were considered as candidate inputs. Only the **CBN NFEM daily NGN/USD exchange-rate series** was downloaded, normalised and integrated into the implemented forecasting comparisons.

The retained snapshot contains 477 raw records and 471 distinct dated observations from 2 December 2024 through 28 October 2026. Identical repeated dates are collapsed; conflicting dated values are rejected. Raw source content, discovery evidence, retrieval metadata and checksums are retained.

The exchange-rate feature is the percentage change between two earlier seven-day window means. It is lagged relative to the forecast origin. This expresses recent currency movement without requiring a fabricated future exchange rate. Its possible relevance to import costs and spending is a hypothesis; a coefficient does not establish a causal economic mechanism.

The source provides observation dates without verified historical release timestamps or vintages. The experiment therefore applies an explicit **seven-day assumed availability lag**. This reduces obvious look-ahead use but does not certify that the downloaded history equals the exact information a forecaster could have obtained at every past origin.

Nivea's review history starts before the economic snapshot. Earlier FX observations were not invented. Economic models require eligible aligned coverage, and the original pilot compared feature sets on common eligible rows. Non-economic candidates remain available if economic data is absent. The retained incumbent's fitting policy also uses a common economic-eligibility restriction where current FX is available, even when the deployed coefficient set excludes FX; this is a comparability policy, not use of FX as a predictor in every model.

CPI, petrol, PMI/business expectations and electricity inputs remain proposals rather than fitted features. Adding all of them immediately would have increased data-alignment work and predictors without enough independent observations to justify it. Monthly/quarterly frequency, release delays and changes in series definitions would also require careful treatment. No broad “Nigerian economy and business-sector model” has yet been implemented.

## 9. Forecasting development: three distinct stages

### 9.1 Existing univariate forecasting

The prototype already contained forecasts for each series separately, using last-value/naive, Holt and damped-Holt methods, with trend testing and numerical safeguards. This could extrapolate review count, sentiment or stars from their own past values. It could not test whether earlier text sentiment improved a later rating or review-count outcome.

That module remains for compatibility and was one review-volume comparator in the pilot. Its statistical intervals and historical trend tests must not be attributed to the current automatic customer outlook. The automatic outlook does not provide calibrated forecast intervals or a probability of business success.

### 9.2 First controlled retrospective pilot

`NLP_Service/business_prediction.py` and supporting scripts added a small, auditable forecasting experiment on the 201-review itel case:

- Cutoff 29 October 2026, excluding the current partial week.
- 193 reviews in 36 completed calendar weeks, with the complete-visible-collection assumption stated.
- Last eight completed target weeks, 31 August–19 October 2026.
- Separate forecasts for a single target week one and four weeks ahead.
- Four-week lookback, ridge regularisation alpha 10 and at least 12 eligible training examples.
- Feature sets: history; history plus sentiment; history plus exchange rate; history plus both.
- Baselines: last observed value and recent mean; the earlier production forecaster additionally compared for review activity.

For counts, the pilot uses the last week's count and recent four-week mean. For stars, it uses the last observed rating and pooled recent customer-star average. Sentiment is pooled across reviews in the lookback. The economic feature is the lagged FX change described above.

Ridge regression was chosen as a manageable, regularised model for the small weekly sample. It learns coefficients from data while penalising large coefficients. It also permits inspection of training means, scales and weights. This was a practical choice; the project has not proved ridge superior to LSTM, Prophet, random forests or every alternative through a common comparison.

Standardisation uses only the current training fold. In simplified notation, with standardised feature matrix Z and centred outcomes y, the fitted coefficient vector is `(ZᵀZ + αI)⁻¹Zᵀy`; prediction adds the training outcome mean. Alpha controls regularisation, while the fitted coefficients control the feature contribution. They are different kinds of “weights.”

Forecast counts are bounded below by zero, and stars to 1–5. Fractional review predictions are expected values, not claims that a fraction of a review will be observed. Bounding prevents impossible outputs but does not by itself prove the model is statistically well calibrated.

### 9.3 Automatic customer-facing forecasting

The user's request to remove backtesting from the site led to `NLP_Service/automatic_forecast.py`. Evaluation remains internal and reproducible; customers do not choose model settings or run a backtest before seeing a forecast.

The candidate policy has 32 configurations:

| Candidate family | Configurations |
| --- | --- |
| Last value | 1 |
| Recent means | 4, 8, 12 and 26 weeks: 4 |
| Exponential smoothing | Rates 0.15, 0.35 and 0.65: 3 |
| Ridge | 4 feature groups × 3 alphas (1, 10, 100) × 2 training windows (26, 104 weeks): 24 |

Ridge candidates can use last target value, four-week mean, up-to-12-week mean, four-week variability and recent slope. Optional columns add pooled text sentiment, sentiment change and lagged exchange-rate change. These richer candidates are distinct from the simpler incumbent/pilot feature definition. The incumbent's alpha-10 history-plus-sentiment policy is refitted separately and can be retained.

Each target and each lead is fitted/selected separately. Each product uses its own history and saved result. Business forecasts use aggregated business history. Thus the **policy is shared**, while coefficients, scaling, available candidates and selected configurations can differ by product, outcome and lead. We did not manually assign a model because one product is a power station and another is a cosmetic product.

Inner candidate selection uses up to 12 preceding target weeks, with at least six eligible selection observations. Ridge requires at least 12 eligible fitting examples. A top-three inverse-MAE blend is considered only if its inner error is lower than the best individual candidate. A regression-containing choice must improve on the best simple inner baseline by at least 5%; otherwise the baseline is kept. These thresholds are policy choices, not established universal constants.

For short usable histories, the system can use a simple recent mean with limited-evidence messaging. It does not force a regression fit or report an invented validation score. Unknown recent coverage or missing target evidence can produce an explicit insufficient-data state.

The first challenger evaluation performed worse than the existing model for several targets. Its failure was retained. The candidate grid was not repeatedly retuned against that outer result to create a flattering score. A subsequent release gate retains the incumbent for each target/lead unless the challenger demonstrates at least **10% lower MAE on at least eight paired historical weeks**. If an incumbent cannot be fitted, an available simple/candidate fallback may be used with the corresponding evidence limitation.

The promotion threshold expresses a preference for a meaningful measured gain before changing the deployed policy. It does not guarantee future improvement and does not guarantee the final policy beats every baseline across all leads.

## 10. Why chronological evaluation was essential

Randomly shuffling weekly rows would allow later business conditions to influence a forecast of an earlier week. Instead, the experiments roll a forecast origin forward through time. For each origin, features, scaling, fitting and selection use only permitted past information.

A training outcome must be fully completed before the origin. This matters especially for longer horizons: a row with old input dates can still have a future target that is not yet known. The implementation excludes such rows rather than merely checking the input date.

The automatic challenger uses nested walk-forward selection: candidate selection is repeated inside each outer historical origin, using preceding weeks. An earlier evaluated outcome may enter a later origin's training after it has actually become available. This is valid chronological updating, not random access to future outcomes.

The deployed interface displays four complete future weeks. Because the unfinished current week is omitted, the four direct leads are **2, 3, 4 and 5 from the last completed week**. For the retained 29 October snapshot, the displayed future Mondays are 2, 9, 16 and 23 November 2026. They are predictions of each individual week's outcome, not four-week cumulative totals.

Automatic outer comparisons cover 12 recent target weeks at those four leads: normally 48 predictions per target. Those are overlapping leads over 12 weeks, **not 48 independent test weeks**.

Tests additionally change unseen future reviews and exchange rates and assert that earlier predictions/scalers do not change. This directly checks a class of future-information leakage, rather than relying only on visual inspection.

## 11. Measured results and their interpretation

### 11.1 Error measures

Mean absolute error is `MAE = mean(|actual − predicted|)`. Root mean squared error is `RMSE = sqrt(mean((actual − predicted)²))`. MAE has an easily understood unit; RMSE gives more influence to large misses. Percentage errors were not the main criterion because sparse weekly counts can be zero.

An MAE of 3.66 reviews/week means an average absolute miss of about 3.66 reviews across the reported predictions. It is not 96.34% accuracy. A rating MAE of 0.14 means about 0.14 star points, not 86% classification accuracy.

### 11.2 First pilot: review activity

| Model | One-week MAE | Four-week MAE |
| --- | ---: | ---: |
| Last value | 2.6250 | 5.1250 |
| Recent mean | 3.5000 | 5.9062 |
| Earlier production forecaster | 2.6250 | 5.6159 |
| History regression | 3.0884 | 4.4349 |
| History + sentiment | 3.1167 | 3.7567 |
| History + FX | 3.1903 | 4.4681 |
| History + sentiment + FX | 3.2159 | 3.7994 |

In this eight-week pilot, adding sentiment reduced four-week review-count MAE by **15.29% relative to history regression**, and the history-plus-sentiment model was **33.11% lower than the earlier production forecaster** at that horizon. Last value/the earlier forecaster were better at one week. FX did not improve count prediction beyond sentiment alone on this block.

### 11.3 First pilot: customer ratings

| Model | One-week MAE | Four-week MAE |
| --- | ---: | ---: |
| Last value | 0.3781 | 0.4265 |
| Recent mean | 0.3480 | 0.3256 |
| History regression | 0.3487 | 0.3111 |
| History + sentiment | 0.3200 | 0.2882 |
| History + FX | 0.3523 | 0.3117 |
| History + sentiment + FX | 0.3234 | 0.2843 |

Sentiment improved these rating comparisons. FX added a small four-week gain over sentiment alone, but this is insufficient evidence for a general causal or economic-effect claim.

### 11.4 Released automatic policy: different protocol

The following is the later release comparison over 12 recent target weeks and leads 2–5, against the previously deployed alpha-10 history-plus-sentiment ridge policy:

| Scope | Target | Previous MAE | Released retrospective MAE | Relative reduction |
| --- | --- | ---: | ---: | ---: |
| Combined research workspace | Reviews/week | 3.836 | 3.660 | 4.6% |
| Combined research workspace | Stars | 0.152 | 0.140 | 7.9% |
| itel | Reviews/week | 3.678 | 3.678 | 0.0% |
| itel | Stars | 0.331 | 0.331 | 0.0% |
| Nivea | Reviews/week | 4.606 | 4.606 | 0.0% |
| Nivea | Stars | 0.315 | 0.297 | 5.6% |

These numbers must not be substituted into the earlier pilot table. The target weeks, horizons, comparison policy and selection procedure differ.

The release snapshot demonstrates the product/lead distinction concretely: itel retains the incumbent for both outcomes at all four leads. Nivea review activity also retains it throughout; Nivea ratings use exponential smoothing at lead 3 and a sentiment ridge candidate at lead 4, while retaining the incumbent at leads 2 and 5. These are snapshot decisions, not permanent product settings.

A further limitation visible in the retained release evidence is that the four-week mean has **0.283** pooled MAE for Nivea ratings versus **0.297** for the released policy. Thus the release does not uniformly beat every simple baseline. The gate compares challenger and incumbent by lead and can retain a policy that is worse than a separately pooled baseline comparison. This should be reported, not hidden behind the improvement relative to the incumbent.

### 11.5 What can and cannot be claimed

The outer historical block was subsequently used by the promotion gate. It is therefore **validation/model-selection evidence, not an untouched final test of the deployed system**. A future prospective period or a new untouched evaluation block is needed for independent post-release performance claims.

The supported result is that sentiment provided predictive value for particular outcomes/horizons in a small retrospective case study, and that the release policy recorded selective retrospective improvements relative to its incumbent. It is not evidence of universally optimal forecasts, commercial prediction, causal effects or nationwide generalisation. Increasing complexity did not automatically improve results.

## 12. Backend integration and import reliability

The Python outlook was connected to authenticated Laravel business/product endpoints. Laravel assembles weekly data, derives trusted coverage/cutoff from product metadata, validates prediction response shapes/dates/domains and saves results with input fingerprints and model-revision information.

Unchanged automatic results are cached for up to 24 hours. New reviews, scoring or changed coverage can invalidate them. Refresh can explicitly recompute. If the prediction service fails, a previously saved good result is retained rather than overwritten with an invalid response. Caching reduces repeat computation without pretending that an old collection contains new weeks.

An actual 1,000-record import exposed PHP's execution-time limit. Records were saved before inference completed, leaving reviews pending and an HTTP 500 that also appeared in the browser as a CORS failure. This was addressed at the ingestion/inference boundary instead of treating every message as just an origin-setting problem.

The revised behaviour is:

- The API accepts a validated batch of up to 1,000 records.
- It saves/deduplicates first and scores a bounded group of at most 50 submitted pending reviews per request.
- The frontend sends sequential 50-record groups and displays progress.
- Product-scoped recovery endpoints and Resume scoring process remaining reviews.
- Retries preserve completed sentiment results and skip repeated stable source IDs within a product.
- Pending, partially processed and service-unavailable states return structured JSON with appropriate CORS behaviour.
- Optional forecast resources are requested only when indicated as present, avoiding expected no-result 404 noise.

The pending 1,000 Nivea records were recovered and the remaining 532 imported/scored. Reimporting the first file added no duplicate records. All original source text, dates and stars were preserved.

The choice of bounded synchronous continuation avoided adding a full queue infrastructure for imports. It has a practical limit: browser-driven continuation pauses when the page closes; saved progress remains recoverable. The product tracking process can score successive groups independently of that page.

## 13. Business accounts, products and administration

The data model was changed to **account → business → products → reviews → sentiment result**. This follows the user's actual workflow: owners sign in, see a combined overview, open products and import into the relevant product.

The business overview contains review summaries, historical signals, automatic business forecasts and product comparison cards. Imports, manual entry, scoring recovery, coverage and tracking controls live on product dashboards. This keeps data attached to its product and prevents the overview from mixing product input operations.

Business totals pool underlying reviews rather than averaging product summaries. Product forecasts use only that product's data and are saved separately from the combined business outlook.

Authentication uses business-owner sessions with hashed bearer tokens, expiry and revocation. Passwords are handled through the backend's hashing facilities. Business/product/review/import/scoring/forecast/tracking routes enforce ownership. A batch explicitly naming another product/business is rejected before partial writes. Registration/login are rate limited. This is a tested prototype access model, not a completed production security audit.

The first release supports one owning business per account. Password recovery, email verification, invitations and more detailed staff roles remain future work.

The legacy admin login broke during the account migration. Separate admin authentication and a management page were restored while preserving stored credentials. Admin tokens and business tokens are not interchangeable. A legacy local demo fallback is restricted to the local environment and loopback and cannot override a stored administrator password. Admin business-record creation does not silently create owner credentials.

Before the research data move, database/review snapshots were saved. An idempotent preparation command moved the public cases into separate product records, retained original reviews/scores and archived legacy business rows. The combined demo does not assert shared real seller ownership. Re-running preparation does not duplicate the research data or overwrite an existing user's password.

## 14. Product monitoring worker

The launcher starts a backend tracking worker. Products begin with tracking off. Owners can configure a supported HTTPS Jumia product/review URL, enable tracking, choose an interval and schedule Check now.

The worker atomically claims a due product, invokes the existing collector with bounds, checks source identity, retains artifacts, imports new source IDs into that product, scores pending reviews in groups and refreshes an existing product outlook when possible. The ordinary dashboard requests automatic outlooks when needed and can reflect the changed data.

On access failure, the worker reports an error and retains the last successful snapshot. A limited/partial collection is identified as incomplete rather than silently becoming complete coverage. It does not solve challenges or fabricate later records. Status and last/next check times are shown. The frontend checks an ownership-scoped activity fingerprint every 30 seconds while tracking is enabled, preserving form drafts and scroll position when refreshing changed views.

A worker was chosen because collection can take much longer than an ordinary web request. “Check now” schedules work instead of keeping the browser request open throughout pagination. This is a scheduled local process, not a cloud-deployed universal monitoring service. Only Jumia Nigeria has a connector, live source access is not assured, and no live collection starts merely from opening the demo.

## 15. Interface and chart changes

The customer interface now supplies the requested totals: reviews analysed, positive share, average compound score and actual customer stars. Business and product pages show historical graphs and a clearly labelled next-four-weeks outlook. Model/backtest controls were removed from the customer flow, while research code remains available for developer reproduction.

Historical charts support pointer/touch inspection, a crosshair, a point marker and a tooltip with week, value, unit and incomplete/missing-data context. Keyboard users can use arrows, Home/End and Enter; Escape dismisses inspection. Forecast bars show precise estimates as estimates. Missing historical values remain gaps.

Clicking a historical week opens the reviews that actually contributed to the selected metric. Business points include business products; product points retain their product. Sentiment views show scored records, lowest scores first. Rating views show actual star-rated records, including pending text scoring. Activity views show eligible original dated records. The selected period, metric, product and sentiment filter are represented in the URL, survive reload/pagination and use the same Lagos calendar definition as the graph. Full-period summaries are not recalculated from only the current page.

This creates a traceable path from a numerical dip to its original comments. It is evidence inspection, not automatic causal explanation of the dip.

Safari's reported tooltip failure was reproduced as new JavaScript paired with a cached old stylesheet. Reloading the matching styles restored its position and chart dimensions. Both HTML entry pages now include content hashes in local CSS/JS URLs; the launcher updates them and a helper can regenerate them after edits. This prevents this particular stale asset mixture. It does not prove all browser bugs are eliminated.

The first aesthetic revision was rejected by the user. The subsequent reference-based design uses a pale blue-grey canvas, white sidebar/top bar and flat white panels, lighter Roboto typography, smaller rectangular controls, restrained blue/green/violet data accents and a green Add product action. It removes the prominent gradients, oversized display style and decorative treatments from the rejected revision. The reference influenced layout and presentation, while actual product functions and data were retained. No fake notifications, search statistics or reference-image business figures were inserted.

The final presentation layer covers business/product/review pages, forms and admin screens. Light is the default; an explicitly saved dark preference is respected. Responsive checks covered desktop at the reference's 1503px width and phone at 390px. Native Safari loaded the revised layout, and chart navigation, mobile menu, product dialog and theme controls were checked. This is functional/visual verification, not a formal usability study with business participants.

## 16. Project organisation and reproducibility

Scattered files were moved into role-based directories without discarding original data or exploratory work:

| Location | Purpose |
| --- | --- |
| `Frontend/src/` | Application scripts and styles |
| `Frontend/samples/` | Generated UI/import examples |
| `Frontend/scripts/` | Fixture and asset-version helpers |
| `Backend/scripts/` | Backend maintenance utilities, including `update_contract.py` |
| `NLP_Service/tests/` | Automated Python service tests |
| `NLP_Service/experiments/forecasting/` | Earlier exploratory diagnostics, separated from tests |
| `NLP_Service/evaluation/` | Protocols, benchmark/economic inputs and evaluation drivers |
| `NLP_Service/examples/` | Manual API example payloads |
| `Scraper/data/collections/` | Real collections, imports and provenance |
| `Scraper/data/archive/` | Failed pilots and older checks |
| `docs/` | Design, data, testing and release explanations |

`docs/FILE_MOVES.json` records the moves. Existing separate repositories were retained. Dependencies, cached model revisions, data fingerprints, source checksums, fold predictions, scaler values and coefficients support reproduction. Generated result folders, databases and large caches are often ignored by Git, so retaining source code alone will not necessarily retain every defence artifact.

The launcher coordinates local ports/configuration, runs preparation against the separate research database, uses available cached model snapshots, performs service checks and starts the tracking worker. This makes the prototype easier to demonstrate, but does not constitute production hosting/deployment.

## 17. Verification completed during development

The latest **recorded** automated checks in the development account are **61 Laravel tests with 438 assertions**, and **114 Python tests passing with two optional collector browser tests skipped**. These are results recorded at their relevant development stages; the documentation task did not rerun the suites or establish a new combined benchmark. The optional browser fixtures had also been exercised separately during collector development as documented in its README.

The checks cover parsing, pagination, source/exclusion handling, deduplication, response selection, access failures, ownership isolation, token expiry/revocation and admin separation, data migration preservation, real batch limits, resumable scoring and CORS/JSON failure responses, weekly aggregation, independent stars, chronological scaling/fitting, future-outcome invariance, automatic selection/gating, caching, stale-data detection, retaining saved forecasts on service failure and chart-to-review boundaries/filters.

Live checks additionally verified the actual running frontend/Laravel/Python stack, cached pretrained model loading, the 1,733-review research workspace, Nivea import recovery and duplicate-safe reimport, separate product/business results, keyboard/pointer chart interactions, weekly drill-down, Safari rendering and phone layouts without horizontal overflow.

The automatic forecasting release verified all 1,739 existing review/sentiment records were unchanged; this total includes six non-research verification/sandbox records. It is not a new research dataset of 1,739 Jumia reviews. The research corpus remains 1,733 records.

Engineering tests establish behaviour and consistency under tested conditions. They do not establish sentiment classification accuracy, sales prediction validity, external generalisation or future forecast reliability. Browser checks are not a user acceptance study, and fixture collector checks are not proof of continuous live source access.

## 18. What remains unfinished and should appear as limitations

1. **Commercial outcomes:** no sales/orders/revenue/profit data or validated link from reviews to transactions.
2. **Sentiment ground truth:** no independently annotated business-review evaluation set or new measured review-domain accuracy/F1.
3. **Independent forecast test:** the release uses historical validation for promotion; a new prospective period is required for an unbiased deployed-policy assessment.
4. **Generalisability:** only two public product cases, positive rating skew, sparse weeks and no verified seller attribution; the combined business is fictional.
5. **Economic timing and coverage:** one retained FX series, assumed lag, no verified vintages, no fitted CPI/fuel/sector/electricity model and no automatic live macroeconomic-data refresh pipeline.
6. **Source completeness:** visible current history may differ from historical availability, and collector sessions can be blocked.
7. **Uncertainty:** the automatic outlook does not supply calibrated prediction intervals, guarantee its estimates or prove it beats every baseline.
8. **Operational maturity:** local deployment, prototype account features and one collector connector; no demonstrated production scale, extensive security audit or business-user usability study.

Useful next research steps are to agree the outcome with the supervisor, collect a real seller's aligned product/transaction history, independently annotate a review subset, pre-register a prospective forecast evaluation, compare the released policy with all baselines on that untouched period and assess interval coverage. Additional economic/sector features should be tested incrementally for useful out-of-time improvement rather than assumed helpful.

## 19. Suggested placement in the final report

| Report area | Material from this work |
| --- | --- |
| Introduction/problem statement | Difficulty turning customer reviews into actionable future feedback indicators; Nigeria/English–Pidgin context; explicit proxy scope |
| Aim/objectives | Collect dated reviews, analyse text, store by business/product, aggregate weekly, compare forecast features, present automatic estimates and inspect original evidence |
| Literature review | Independently sourced work on sentiment transfer, Nigerian languages, time-series evaluation, economic information timing and review-based outcome limitations. This guide does not replace those citations. |
| Methodology | Data source/cutoff, provenance, deduplication, rating skew, weekly definitions, pretrained routing, signed score, pilot/release protocols and leakage controls |
| System analysis/design | Requirements, component/data flows, ownership model, business/product split, API boundaries, worker and failure states |
| Implementation | Collector modes, imports/recovery, authenticated routes, automatic fitting/gate/cache, frontend and interactive graphs |
| Testing/results | Separate engineering tests from predictive results; include the two distinct result protocols and failed-challenger/baseline findings |
| Discussion/limitations | Proxy validity, no sentiment labels, historical-selection bias, live source restrictions, missing economic vintages and lack of commercial records |
| Future work | Seller outcomes, annotation, prospective evaluation, intervals, wider datasets/connectors and production/account work |

A report-ready implementation paragraph is:

> The system was implemented as a web application with a JavaScript frontend, a Laravel application backend and a Python sentiment and forecasting service. Dated product reviews collected from Jumia Nigeria were retained with their original customer ratings and source provenance. Text sentiment was produced by pretrained classifiers using a marker-based general/Pidgin routing policy. The application aggregates eligible reviews into Lagos calendar weeks and estimates future weekly review activity and mean customer ratings through chronologically fitted forecasting models. Business owners can inspect aggregated results, manage individual products, import reviews and trace historical chart periods to their contributing comments. Model selection and historical checking occur internally, while the customer interface presents forecast estimates and recent historical error.

A report-ready findings paragraph is:

> In the initial eight-week itel retrospective pilot, adding earlier text sentiment reduced four-week-ahead review-count MAE from 4.4349 to 3.7567 relative to the history-only regression, a reduction of 15.29%. The same model did not outperform the simplest comparator at the one-week horizon, and exchange-rate input did not further improve the review-count result. The later automatic release recorded selective improvements relative to its incumbent but retained the incumbent for several targets and did not uniformly outperform all simple baselines. Because the release's historical evaluation block was used for promotion decisions, these results are model-selection evidence rather than an independent final assessment of future deployed accuracy.

## 20. Questions to prepare for the project defence

**What exactly is being predicted?** Future individual-week written-review counts and average actual customer stars. These are feedback activity and reviewer-satisfaction indicators; sales/profit remain outside the validated scope.

**What is the sentiment model's role?** It converts prior text into a numerical feature. The research comparison tests whether that earlier feature adds information beyond prior outcomes. It is not the future outcome label itself.

**Did you train the sentiment model?** The application uses pretrained classifiers and fallback logic. The work fitted forecasting coefficients/configurations; it did not fine-tune the language models on newly annotated reviews.

**Why ridge and simple baselines rather than a complex neural forecaster?** The effective sample is weekly and small, especially for itel. Regularisation, transparent weights and honest baseline comparisons were practical. No untested superiority claim is made against all alternatives.

**Do products use different models?** They use one shared selection policy on separate histories. Their fitted parameters and target/lead choices can differ. A common model family does not imply identical coefficients.

**Why not use all Nigerian economic data?** Only aligned, available data can legitimately enter an historical forecast. One FX series was implemented first; many predictors with few independent time observations risk unstable fitting. Other indicators require release-aware collection and incremental validation.

**Why remove the backtest button?** It is an evaluation function handled internally/offline; owners should receive prepared estimates. Its removal does not mean the model never needs reevaluation or that future accuracy is guaranteed.

**Why exclude the current week?** A partial week is not directly comparable to a full target week. The interface instead forecasts complete future weeks using leads consistent with that omission.

**Can the project claim business growth prediction?** Only if “performance” is explicitly accepted as the declared feedback proxies. A commercial claim requires actual seller outcomes and new validation.

**What is the largest remaining evaluation issue?** No independent human review labels for sentiment, and no untouched prospective evaluation of the promoted forecasting policy. Both are separate from passing software tests.

## 21. Evidence index and reproduction entry points

All paths below are relative to the project root for portable use inside this document.

| Evidence | Location |
| --- | --- |
| Project scope/design evolution | `docs/PROJECT_GUIDE.md`, `docs/PREDICTION_DESIGN.md` |
| Exact collection counts and caveats | `Scraper/data/collections/itel-power-station/DATASET_NOTES.md`, `Scraper/data/collections/nivea-dry-impact/DATASET_NOTES.md` |
| Collector operation/access limitations | `Scraper/README.md`, `Scraper/tests/` |
| Sentiment scoring/routing | `NLP_Service/model.py`, `NLP_Service/preprocessing.py` |
| First pilot method/results | `docs/BACKTEST_RESULTS.md`, `NLP_Service/evaluation/business_prediction/README.md` |
| Pilot model and chronology | `NLP_Service/business_prediction.py`, `NLP_Service/tests/test_business_prediction.py` |
| CBN source/normalisation/timing | `NLP_Service/evaluation/data/economy/README.md` and retained JSON/source files |
| Automatic policy and release caveat | `docs/AUTOMATIC_FORECASTING.md`, `NLP_Service/automatic_forecast.py` |
| Recorded protocol, failed challenger and release evidence | `NLP_Service/evaluation/automatic_forecast/protocol.json`, `challenger_evaluation.json`, `release_evaluation.json` |
| Ownership, migration, worker and admin design | `docs/BUSINESS_WORKSPACES.md`, `Backend/routes/api.php`, `Backend/tests/Feature/` |
| Aggregation and caching | `Backend/app/Services/DashboardService.php`, `OutlookService.php` |
| Imports/scoring/worker | `Backend/app/Services/ReviewScoringService.php`, `ProductTrackingService.php` |
| Recorded checks and UI verification | `docs/APP_VERIFICATION.md`, `.logs/*verification.json` |
| Final design proof | `.logs/screenshots/reference-dashboard.png` |
| File moves | `docs/FILE_MOVES.json` |
| Startup and demonstration | `docs/TESTING_THE_APP.md`, `scripts/dev.py` |

Developer reproduction commands, from the project root:

```sh
# Start the integrated local application.
.venv/bin/python scripts/dev.py

# Software tests; the two live-browser collector fixtures are opt-in.
.venv/bin/python -m pytest NLP_Service/tests Scraper/tests -q

# Automatic forecasting research evaluation (reads the research database).
.venv/bin/python NLP_Service/scripts/evaluate_automatic_forecast.py

# First pilot: choose a fresh output directory and retain its artifacts.
.venv/bin/python NLP_Service/scripts/backtest_business.py \
  --reviews Scraper/data/collections/itel-power-station/reviews.raw.json \
  --as-of 2026-10-29 \
  --output NLP_Service/evaluation/results/business_backtest/itel-report-reproduction
```

Run Laravel tests with `php artisan test` from `Backend/`. The evaluation commands are reproduction tools, not actions the business user needs to perform. Preserve original snapshots and outputs rather than replacing them with later source vintages. Read the dataset/evaluation notes before rerunning a changed protocol.
