import pandas as pd


def extract_total(csv_path):
    """Sum the 'Amount' column of an invoice CSV and return the grand total."""
    df = pd.read_csv(csv_path)
    return float(df["Amount"].sum())
