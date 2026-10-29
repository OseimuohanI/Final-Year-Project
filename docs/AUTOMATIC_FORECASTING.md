# Automatic forecasting release — 29 October 2026

The business app now selects and refits forecasts automatically. Customers see four weekly review-activity/rating estimates, a collection date and recent historical error. There is no model picker, backtest button or evaluation-lead selector. New or changed data invalidates saved forecasts; unchanged results are cached for up to 24 hours. A refresh failure retains the previous saved result.

## Training and selection

This is a forecasting improvement, not supervised retraining of the sentiment classifiers. There are no independent human sentiment labels with which to claim better sentiment accuracy. Ratings retain their original stars; they are not used as sentiment labels.

The candidate policy was recorded before its first evaluation in [protocol.json](../NLP_Service/evaluation/automatic_forecast/protocol.json). It uses 32 candidates: last value, means over 4/8/12/26 weeks, three smoothing rates, and ridge regression with three regularisation strengths, two training windows and four feature groups. Regression learns coefficients and scaling from each training window. Feature groups include history, text sentiment, exchange rates or both. The top three candidates may form an inverse-error-weighted blend. The target and each lead have separate fitted weights.

For each historical forecast origin, candidate selection uses only the preceding twelve target weeks. Every fitting outcome has finished before that origin. The outer evaluation covers twelve recent target weeks at the same four leads used by the app (2–5 weeks after the last completed week). This is nested walk-forward evaluation: an earlier outer outcome may enter training at a later origin after it becomes available. The 48 predictions per target are overlapping leads over twelve weeks, not 48 independent test weeks. This chronological approach follows [Forecasting: Principles and Practice](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation).

The initial challenger policy performed worse than the existing ridge model for several targets. That failure is retained in [challenger_evaluation.json](../NLP_Service/evaluation/automatic_forecast/challenger_evaluation.json). Its feature grid, coefficients procedure and inner-selection policy were not retuned against those outer results. Instead, a release gate was added: for each target/lead, the challenger replaces the refitted incumbent only with at least 10% lower absolute error over at least eight paired historical weeks. Otherwise the incumbent stays. If the incumbent cannot be fitted, the available candidate/simple estimate is used with limited-evidence messaging.

**The outer historical block is now used by the promotion gate. It is validation/model-selection evidence, not an untouched final test of the deployed system.** The app says this explicitly. A new, prospective period is needed for an independent post-release accuracy claim. Improvements below describe the retrospective gate, and must not be presented as guaranteed future improvement.

## Observed results

MAE is average absolute error; lower is better. The reference is the previously deployed history-plus-sentiment ridge policy with alpha 10. Both policies use the same observed target weeks/leads.

| Workspace | Target | Previous MAE | Released historical MAE | Reduction |
| --- | --- | ---: | ---: | ---: |
| Pulseboard Research Demo | Reviews/week | 3.836 | 3.660 | 4.6% |
| Pulseboard Research Demo | Stars | 0.152 | 0.140 | 7.9% |
| itel Power Go portable power station | Reviews/week | 3.678 | 3.678 | 0.0% |
| itel Power Go portable power station | Stars | 0.331 | 0.331 | 0.0% |
| Nivea Dry Impact roll-on · pack of 3 | Reviews/week | 4.606 | 4.606 | 0.0% |
| Nivea Dry Impact roll-on · pack of 3 | Stars | 0.315 | 0.297 | 5.6% |

Itel has 201 reviews across 36 completed calendar weeks; Nivea has 1,532 saved reviews across 235 completed calendar weeks (1,529 in completed weeks). The fictional combined research workspace has 1,733 reviews. It does not establish a shared real seller. Current-week reviews are excluded; original dates and ratings are preserved. Unknown collection weeks remain unknown, rather than fabricated zeros. The current source collections assume completeness for visible reviews, which does not establish that deleted/unavailable historic reviews are represented.

## Reproduction and artifacts

```bash
.venv/bin/python NLP_Service/scripts/evaluate_automatic_forecast.py
.venv/bin/python -m pytest NLP_Service/tests Scraper/tests -q
cd Backend
php artisan test
```

The evaluation script reads SQLite in read-only mode. It records data fingerprints, source cutoff, the protocol hash, paired comparisons, future predictions, learned coefficients, scaling and ensemble weights. Full fold diagnostics and weekly inputs are in `NLP_Service/evaluation/results/automatic-forecast/` (ignored generated artifacts). A compact release snapshot is checked in as [release_evaluation.json](../NLP_Service/evaluation/automatic_forecast/release_evaluation.json). The old research endpoints remain available for developer reproduction; the customer interface uses automatic mode.

`POST /api/businesses/{id}/outlook/generate` and `POST /api/products/{id}/outlook/generate` accept an empty body or `{"model":"auto"}`. Collection cutoff and coverage come from server-side product metadata. Optional `{"refresh":true}` recomputes. The worker refreshes automatic product forecasts following successful new collection/scoring. The dashboard requests automatic forecasts on arrival and after imports/updates. Coverage controls are part of product-data management.

API output includes each point’s model weights and fit; recent-error metadata is marked `used_for_promotion: true` and `independent_final_test: false`. Large historical prediction lists stay in offline diagnostics instead of dashboard responses. Missing ratings or insufficient known history produce an explicit insufficient-data state. Service failures do not replace a good saved result.

Forecasts still measure public feedback activity and actual customer ratings, not sales, revenue, profit, causal economic effects or a success probability. Exchange-rate data has an assumed seven-day availability lag and no verified publication vintages. No calibrated uncertainty interval is claimed.
