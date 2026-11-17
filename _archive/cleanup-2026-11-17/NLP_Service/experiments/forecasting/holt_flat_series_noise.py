import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.exponential_smoothing import ExponentialSmoothing

series = pd.Series([1.0]*8)
if series.var() < 1e-8:
    series += np.random.normal(0, 1e-4, len(series))
    
mod = ExponentialSmoothing(series, trend=True, damped_trend=False)
res = mod.fit(disp=False)
print("AIC:", res.aic)
print("Forecast:", res.get_forecast(steps=4).conf_int(alpha=0.2))
