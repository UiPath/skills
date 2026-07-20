"""Order-import helpers for the PyOrderImport process.

clean_records-style functions are defined at module level so Load Python Script
can bind them and Invoke Python Method can call import_orders.
"""


def import_orders(csv_path="orders.csv"):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as handle:
        for line in handle:
            cells = [c.strip() for c in line.split(",")]
            if any(cells):
                rows.append(",".join(cells))
    return "\n".join(rows)


# --- module-level configuration executed at import time ---
DEFAULT_DISCOUNT = 100 / 0
print("default discount:", DEFAULT_DISCOUNT)
