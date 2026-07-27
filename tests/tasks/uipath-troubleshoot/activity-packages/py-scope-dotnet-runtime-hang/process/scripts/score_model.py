"""Scoring helpers for the PyScoreModel process.

score() is defined at module level so Load Python Script can bind it and Invoke
Python Method can call it.
"""


def score(features=None):
    features = features or [0.2, 0.5, 0.3]
    weights = [0.5, 0.3, 0.2]
    return round(sum(f * w for f, w in zip(features, weights)), 4)
