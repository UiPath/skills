"""Batch-aggregation helpers for the PyBatchAggregate process.

aggregate() is defined at module level so Load Python Script can bind it and
Invoke Python Method can call it.
"""


def aggregate(rows=None):
    rows = rows or []
    return {"count": len(rows), "total": sum(rows)}


# --- module-level warm-up executed at import time ---
# Load Python Script runs the module body, so this builds a 5M-entry lookup AND
# prints every row to stdout at load. The stdout flood saturates the engine pipe
# and the scope never returns within the 30s Timeout.
_LOOKUP = {}
for _i in range(5_000_000):
    _LOOKUP[_i] = _i * _i
    print("warmup row", _i, "=>", _LOOKUP[_i])
