"""Data-cleaning helpers invoked by the PyDataTransform process.

Functions are defined at module level so Load Python Script can bind them and
Invoke Python Method can call clean_records.
"""


def clean_records(csv_path="input.csv"):
    """Strip blank rows and trim whitespace; return the cleaned CSV as text."""
    rows = []
    with open(csv_path, "r", encoding="utf-8") as handle:
        for line in handle:
            cells = [cell.strip() for cell in line.split(",")]
            if any(cells):
                rows.append(",".join(cells))
    return "\n".join(rows)
