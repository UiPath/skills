"""Local helper module imported by ledger_sync.py (same scripts/ folder)."""


def normalize(entries):
    return [str(e).strip() for e in entries if str(e).strip()]
