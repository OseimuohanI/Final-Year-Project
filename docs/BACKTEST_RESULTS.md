# First measured business prediction backtest

Completed on 29 October 2026. This is an offline retrospective pilot on one product, using the existing 201 real itel IESS-320T reviews and official CBN daily exchange rates. The Nivea listing is a possible replication case and was not part of this run.

## Main findings

- Adding text sentiment reduced four-week-ahead review-volume MAE by **15.29%** relative to the history-only regression.
- The history-and-sentiment model reduced that error by **33.11%** relative to the existing production forecaster.
- The last-value baseline and existing forecaster were better for one-week-ahead review volume.
- Exchange-rate changes did not improve review-volume forecasts beyond sentiment alone on these eight test weeks.
- Customer-rating errors also fell with sentiment. Adding FX gave a small additional improvement at the four-week horizon, which is too little evidence for a general economic-effect claim.

Lower MAE means smaller average absolute prediction error. Volume errors are in reviews per week; rating errors are in customer-star points. A four-week horizon predicts the individual week four weeks ahead, not the total over four weeks.

## Review-volume results

| Model | One-week MAE | Four-week MAE |
| --- | ---: | ---: |
| last_value | 2.6250 | 5.1250 |
| recent_mean | 3.5000 | 5.9062 |
| current_forecaster | 2.6250 | 5.6159 |
| history | 3.0884 | 4.4349 |
| history_sentiment | 3.1167 | 3.7567 |
| history_economy | 3.1903 | 4.4681 |
| history_sentiment_economy | 3.2159 | 3.7994 |

## Customer-rating results

| Model | One-week MAE | Four-week MAE |
| --- | ---: | ---: |
| last_value | 0.3781 | 0.4265 |
| recent_mean | 0.3480 | 0.3256 |
| history | 0.3487 | 0.3111 |
| history_sentiment | 0.3200 | 0.2882 |
| history_economy | 0.3523 | 0.3117 |
| history_sentiment_economy | 0.3234 | 0.2843 |

## Data and method

- 201 reviews scored with the existing general pretrained sentiment model, pinned at revision `f2f1202b1bdeb07342385c3f807f9c07cd8f5cf8`. No existing Pidgin markers were detected in this cohort.
- Customer stars were kept independent of text sentiment. There are no human reference sentiment labels, so classifier accuracy is not claimed.
- Eight reviews from the current partial week were excluded from forecasting: 193 reviews contributed to 36 completed calendar weeks, including two zero-review weeks.
- Eight completed test target weeks: 31 August–19 October 2026. Each model/horizon has eight evaluated predictions with no skipped target weeks.
- Four fixed regression feature sets, alpha 10, a four-week lookback, and at least 12 eligible training examples. Hyperparameters were not tuned against these transformer holdout results.
- Scaling and model fitting occur within each training fold. A training target must have completed before the forecast origin, including for the four-step horizon.
- The CBN endpoint returned 477 records, normalised to 471 distinct dated observations. A seven-day availability lag was assumed because historical publication timestamps/vintages are unavailable.
- The current production forecaster is compared using only its past count series. This experiment does not automatically replace dashboard forecasts.

## Interpretation

The supported finding is an error reduction for a declared public-feedback outcome in this small case study. The results do not establish sales, revenue, profitability, causation, or a probability of business success. Dependence between time periods, sparse weekly reviews, current visibility of historical reviews, and unavailable economic vintages limit generalisation. The next research step is a separately collected product/time period, keeping this experiment as the first pilot.

## Artifacts and reproduction

- [Full report](../NLP_Service/evaluation/results/business_backtest/itel-2026-10-29/REPORT.md)
- [Fold-by-fold results and availability audits](../NLP_Service/evaluation/results/business_backtest/itel-2026-10-29/backtest.json)
- [Chart](../NLP_Service/evaluation/results/business_backtest/itel-2026-10-29/review_volume_backtest.png)
- [Method and commands](../NLP_Service/evaluation/business_prediction/README.md)
- [Implementation](../NLP_Service/business_prediction.py)
- [Official CBN source page](https://www.cbn.gov.ng/rates/exchratebycurrency.html)

The model/data/code hashes and detailed metrics are recorded with the artifacts. Generated result folders and model caches are ignored by Git; preserve them with the project for the defence.
