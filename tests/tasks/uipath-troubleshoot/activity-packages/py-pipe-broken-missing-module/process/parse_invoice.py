def extract_total(csv_path):
    """Sum the 'Amount' column of an invoice CSV and return the grand total."""
    import pandas as pd

    df = pd.read_csv(csv_path)
    return float(df["Amount"].sum())
