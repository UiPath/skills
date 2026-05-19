"""Shared manifest helpers for tracking and cleaning up tenant resources created by pre_run + agent.

JSONL format, one record per line:
    {"kind": "folder", "key": "<guid>", "extra": {"path": "Shared/e2e-..."}}
    {"kind": "process", "key": "<guid>", "extra": {"folder_path": "Shared/e2e-..."}}

Append-only — partial reads on crash leave a recoverable file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

MANIFEST_FILE = "created-resources.jsonl"


def append(kind: str, key: str, **extra: Any) -> None:
    """Append a resource record to created-resources.jsonl in CWD."""
    record = {"kind": kind, "key": key}
    if extra:
        record["extra"] = extra
    with open(MANIFEST_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def load(path: str | Path = MANIFEST_FILE) -> list[dict]:
    """Load all records from a manifest file. Returns [] if missing."""
    p = Path(path)
    if not p.is_file():
        return []
    records = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            # Skip malformed lines — best-effort recovery
            continue
    return records


# Deletion order — deepest dependencies first. Lower index runs earlier.
# (Folders last because they're the parent of most other resources.)
DELETE_ORDER = [
    "bucket-file",
    "queue-item",
    "trigger",
    "webhook",
    "asset",
    "library",
    "bucket",
    "queue",
    "process",
    "package-version",
    "role",
    "deploy",
    "solution-package",
    "folder",
]


def sort_for_deletion(records: list[dict]) -> list[dict]:
    """Return records sorted by deletion order. Unknown kinds run last."""
    def order(r: dict) -> int:
        kind = r.get("kind", "")
        return DELETE_ORDER.index(kind) if kind in DELETE_ORDER else 999
    # Within the same kind, deeper folders first (longer path = deeper)
    def secondary(r: dict) -> int:
        extra = r.get("extra") or {}
        path = extra.get("path") or extra.get("folder_path") or ""
        return -len(path)  # longer first
    return sorted(records, key=lambda r: (order(r), secondary(r)))
