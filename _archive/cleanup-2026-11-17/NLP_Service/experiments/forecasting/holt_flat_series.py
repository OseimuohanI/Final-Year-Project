import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

series = pd.Series([1, 1, 1, 1, 1, 1, 1, 1])
mod = ExponentialSmoothing(series, trend="add", damped_trend=True)
res = mod.fit(optimized=True)
print("Classic AIC:", res.aic)
print("Classic damping:", res.params['damping_trend'])
