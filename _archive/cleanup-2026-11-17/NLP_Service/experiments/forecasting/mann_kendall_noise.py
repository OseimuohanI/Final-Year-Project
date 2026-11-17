import pymannkendall as mk
import numpy as np
series = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
series = [x + np.random.normal(0, 0.01) for x in series]
print(mk.hamed_rao_modification_test(series, alpha=0.10))
