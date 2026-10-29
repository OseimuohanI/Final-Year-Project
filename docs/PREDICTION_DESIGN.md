# Forecasting business outcomes using sentiment and Nigerian economic context

Design proposal, researched on 29 October 2026. This document proposes an experiment; it does not report a fitted economic model, downloaded macroeconomic dataset, or measured forecast improvement.

**Implementation update:** the proposed offline comparison has now been implemented and run on the 201-review case study with official CBN FX data. See [measured results](BACKTEST_RESULTS.md) and [reproduction instructions](../NLP_Service/evaluation/business_prediction/README.md). The remainder preserves the design rationale, candidate sources, and limitations; sources other than NFEM FX remain candidates rather than inputs to this first run.

## The proposed research question

> Does combining historical customer sentiment with Nigerian economic indicators improve short-term prediction of an observable outcome for the selected online business or product case study?

Economic indicators are candidate inputs. We still need an independently observed outcome to learn from and later check. National economic conditions cannot substitute for a seller's missing sales or profit records.

## Choose what performance means

| Candidate outcome | What we have | What a forecast could establish |
| --- | --- | --- |
| Weekly sales/orders/revenue | No seller-level history | Commercial performance, if actual records are obtained and predictions are validated |
| Weekly number of published text reviews | Available for the selected product | Public feedback activity; its usefulness as a sales/demand proxy is unverified |
| Average actual customer star rating in a future period | Available, with sparse weeks | Satisfaction among customers who publish rated reviews |
| A self-defined business health score | No independent reference outcome | A transparent descriptive/scenario score, not validated commercial success |

For a public-data-only pilot, propose **published review volume as the primary observable outcome**, with **future actual customer ratings as a secondary satisfaction outcome**. This is a proposed proxy-based scope, subject to agreement with the supervisor. If the topic requires commercial performance, sales/order/revenue history is still necessary.

Do not equate review volume with sales, product feedback with a seller's entire business, or increasing sentiment with profit growth. Review publication can lag a purchase, and participation in reviewing can change independently of demand.

## What the current code measures

`NLP_Service/forecasting.py` forecasts weekly sentiment, ratings, and review counts as separate series. It does not use earlier sentiment as a predictor of later review volume/ratings, and does not accept economic predictors.

Its Mann–Kendall direction describes a trend in the historical input series. It is not an evaluated probability that a business will grow. A future-facing dashboard direction should eventually be tied to the forecasted outcome over a declared horizon, with uncertainty and a reference period.

The sentiment service uses pretrained classifiers. The forecasting extension would learn the relationship between time-varying inputs and later outcomes; it would not train on generated review fixtures or fabricate economic values.

## Public sources checked

Availability below means a publisher/source was verified, not that a complete compatible historical series has already been retrieved.

| Source | Candidate input and frequency | Potential role and availability limits |
| --- | --- | --- |
| [CBN NFEM exchange rates](https://www.cbn.gov.ng/rates/exchratebycurrency.html) | Official daily NGN/USD rate; derive a past-week change or volatility | Candidate import-cost context; historical date coverage and publication timing need inspection |
| [NBS CPI reports and tables](https://microdata.nigerianstat.gov.ng/index.php/catalog/154/related-materials) | Monthly CPI/inflation; possibly an appropriate component | Candidate price/household-budget context. Store the reference month, release date, and series definition |
| [NBS PMS price watch](https://microdata.nigerianstat.gov.ng/index.php/catalog/157/related-materials) | Monthly retail petrol prices, including geographic detail | Candidate transport/backup-power context. The catalogue inspected lists 2026 releases through May; a complete series through the review end date has not been established |
| [CBN Purchasing Managers' Index](https://www.cbn.gov.ng/documents/PurchManIndex.html) and [Business Expectations Survey](https://www.cbn.gov.ng/Documents/BusExpSurvReport.html) | Candidate business/sector survey indicators | Official publication pages exist; historical files, present sector classifications, release dates, and suitable coverage still need checking |
| [NBS electricity reports](https://microdata.nigerianstat.gov.ng/index.php/catalog/171/related-materials) | Electricity/distribution statistics reported by quarter | Background context for a power product. The inspected package covers Q4 2024–Q4 2025 and was released in June 2026; it is not a real-time local outage series |

For the first experiment, start with **one exchange-rate feature**, then test whether adding one CPI feature is supported by the amount of data. Other sources remain candidates. Their economic relevance is a hypothesis, not evidence of predictive improvement.

The CPI catalogue documents rebasing to a 2024 price reference and 2023 expenditure weights. Record definitions and revisions rather than joining incompatible old and new series by date alone. The catalogue lists the September 2026 CPI release date as 15 October 2026: a forecast made on 1 October could not legitimately use that release.

## Sector context for the current case study

For the portable power station, plausible hypotheses include:

- Exchange-rate movements may affect import/replacement costs and pricing, depending on the supply chain.
- Petrol prices may change the relative attraction of a battery backup product, while wider household cost pressure may reduce the ability to buy it.
- Price changes, promotions, stock availability, and product reliability may affect review activity and customer ratings.

These effects can conflict and vary over time. Do not hard-code a positive or negative coefficient or invent a percentage uplift. The present review collection does not contain historical product prices, promotions, stock changes, or seller order records. A current product-page snapshot cannot fill those historical gaps.

## What our current dataset can support

The preserved import contains **201 deduplicated product reviews**, dated 17 February–28 October 2026. Rechecking it gives:

- 37 calendar weeks, of which 35 have at least one review.
- Nine calendar months represented.
- Eleven observed weeks with only one or two reviews.
- A partial last week beginning 26 October 2026.

There are not 201 independent weekly training observations. A model using weekly outcomes has roughly the weekly history above, before losing rows to lags and evaluation periods. Repeating a monthly CPI value across several weeks does not create additional independent monthly economic observations.

Use this as a small feasibility pilot. Avoid a model with many predictors or annual seasonality learned from less than one year. More historical reviews can extend the time dimension; related product series can support a later panel model, but shared national indicators still provide only the same limited number of distinct time periods.

For missing weeks, distinguish a verified zero review count from an unknown collection gap. Do not invent a rating or sentiment observation for a week with no reviews. Carrying a past value forward for numerical modelling must remain explicitly marked as an assumption. Exclude incomplete target weeks from scored evaluation.

## The experiment

Create one modelling row per completed calendar week. Use only predictors available before the prediction origin:

```text
Past review volume and customer ratings
Past sentiment summaries, including negative-feedback share
Published economic indicators available at that time
                         |
                         v
                Small forecasting model
                         |
                         v
       Predicted future review activity / customer rating
                         |
                         v
        Compare with subsequently observed outcomes
```

Begin with next-week prediction to establish whether the model works at all; assess a four-week outlook separately. Do not assume that one-step accuracy proves four-step accuracy.

Compare feature sets on exactly the same time periods, horizon, and evaluation procedure:

1. History only.
2. History plus sentiment.
3. History plus economic inputs.
4. History plus sentiment and economic inputs.

Also retain a simple last-value/recent-average forecast as a benchmark. These comparisons test both the contribution of sentiment and the additional contribution of economic context. Begin with a small regularised model rather than choosing complexity to match the number of available data sources. Any count model must produce nonnegative expected counts; rating outputs must respect the 1–5 domain.

For review activity, start with past count and one sentiment summary, then one exchange-rate change. Avoid simultaneously fitting a large set of overlapping sentiment measures, many lags, CPI components, and sector variables to this short history.

## Make a genuine forecast

1. **Use publication dates.** An indicator becomes usable when published, not at the start/end of the month it describes. Keep `reference_period`, `published_at`, `retrieved_at`, `unit`, `series_id`, and revision/vintage information with source data.
2. **Keep the future unseen.** Develop using earlier weeks, evaluate on later complete weeks, and roll prediction origins forward. Fit feature scaling, imputation, and model choices only on the training portion at each origin.
3. **Handle unknown future inputs explicitly.** Future realised exchange rates or later CPI releases cannot be supplied to a historical forecast. For a four-week forecast, use predictors known at the origin, a documented carry-forward assumption, a separately generated predictor forecast, or a labelled scenario. A next-week predictor set cannot silently consume future observations at later horizons.
4. **Measure performance against the target.** Report MAE and RMSE in reviews or rating points and compare them with the benchmark. With sparse, zero-valued counts, avoid relying on percentage errors. Assess interval coverage if there are enough held-out forecasts.
5. **Let the outcome decide.** If economics does not improve out-of-time accuracy, report that result and retain the better simpler model. An estimated relationship or attractive chart does not establish predictive usefulness or causation.

If the short history cannot support stable model comparison, report the feasibility limitation, extend the data, or narrow the claim. Do not turn a failed validation into an invented business-success score.

## Forecasts and scenarios serve different purposes

A validated forecast estimates a later observable quantity using information available now. A scenario asks how that estimate changes under assumed conditions, such as a specified exchange-rate change. Scenarios should state assumptions and should not be presented as probabilities or demonstrated causal effects.

The eventual dashboard can show the target/horizon, point forecast and interval, latest economic input periods, and measured baseline comparison. It should identify whether a displayed result is an evaluated forecast, an unvalidated pilot, or a conditional scenario.

## Recommended next implementation milestone

Build the **weekly evaluation dataset and simple benchmark** first. Join one verified economic series by its availability date, add lagged sentiment after scoring reviews, and test the nested feature sets. Keep the existing production forecast unchanged until a reproducible experiment shows what the new model can claim.

The research contribution is the measured comparison: whether customer sentiment, and then economic context, adds predictive information about a declared future outcome in this Nigerian case study.
