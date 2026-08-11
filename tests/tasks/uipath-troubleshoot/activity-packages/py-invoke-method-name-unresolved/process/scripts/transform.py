"""Record-cleaning script for PyRecordCleaner.

Run directly to clean input.csv:
    python transform.py
"""

import csv

if __name__ == "__main__":

    def clean_records(csv_path="input.csv"):
        """Strip blank rows and trim whitespace; return the cleaned CSV text."""
        with open(csv_path, newline="", encoding="utf-8") as handle:
            rows = [row for row in csv.reader(handle)]
        cleaned = [
            ",".join(cell.strip() for cell in row)
            for row in rows
            if any(cell.strip() for cell in row)
        ]
        return "\n".join(cleaned)

    print(clean_records())
