import pandas as pd
from statsmodels.tsa.statespace.exponential_smoothing import ExponentialSmoothing

# synthetic data
data = pd.Series([1, 2, 3, 4, 5, 2, 3, 4, 5, 6, 7])
try:
    mod = ExponentialSmoothing(data, trend=True, damped_trend=True)
    res = mod.fit()
    pred = res.get_forecast(steps=3)
    ci = pred.conf_int(alpha=0.2)
    print("DAMPED WORKED")
    print(ci)
except Exception as e:
    print(f"FAILED: {e}")
