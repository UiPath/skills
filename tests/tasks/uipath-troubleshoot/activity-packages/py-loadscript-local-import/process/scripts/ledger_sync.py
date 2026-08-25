"""Ledger-sync entry module for the PyLedgerSync process.

Depends on the sibling helper module ledger_utils.py in this same scripts/ folder.
"""

import ledger_utils   # local sibling module in this scripts/ folder


def sync(entries=None):
    entries = entries or []
    return "\n".join(ledger_utils.normalize(entries))
