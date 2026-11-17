from statsmodels.tsa.statespace.exponential_smoothing import ExponentialSmoothing
import pandas as pd
data = pd.Series([1, 2, 3, 4, 5, 2, 3, 4, 5, 6, 7])
mod = ExponentialSmoothing(data, trend=True, damped_trend=True)
mod.bounds[2] = (0.8, 0.98) # edit the 3rd bound!
res = mod.fit()
print(res.params)
