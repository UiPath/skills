"""Forecasting helpers for the PyForecast process.

forecast() is defined at module level so Load Python Script can bind it and
Invoke Python Method can call it.
"""


def forecast(series=None, periods=3):
    series = series or [1.0, 2.0, 3.0]
    last = series[-1]
    step = (series[-1] - series[0]) / max(len(series) - 1, 1)
    return [round(last + step * (i + 1), 3) for i in range(periods)]
