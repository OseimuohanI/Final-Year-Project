# Exploratory scripts

`forecasting/` contains the original one-off investigations of Holt forecasting, flat-series noise, state-space bounds, and Mann–Kendall behaviour. They print diagnostic output and are not automated tests or evaluation results.

The scripts were moved from the service root without changing their experiments. Run one from the project root using the existing environment, for example:

```bash
.venv/bin/python NLP_Service/experiments/forecasting/holt_flat_series.py
```

Production forecasting remains in `NLP_Service/forecasting.py`; automated tests are in `NLP_Service/tests/`.
