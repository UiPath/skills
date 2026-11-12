#!/usr/bin/env python3
"""Helper for copy_taxonomy.yaml: Extract Credit Note's processorKey is its own.

Passes when extractCreditNote1 has no processorKey (a CLI that does not provision
on `nodes schema set`), or has one that is not extractInvoice1's and that an
idpProcessor resource in the solution declares (a CLI that does). Fails on a key
copied from Extract Invoice, and on a key no processor resource names, since a
synthesised key points at nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FLOW = Path("BillingDocs", "BillingDocs", "BillingDocs.flow")
RESOURCES = Path("BillingDocs", "resources")
TARGET, SOURCE = "extractCreditNote1", "extractInvoice1"


def _processor_key(flow: dict, node_id: str) -> str | None:
    for node in flow.get("nodes") or []:
        if node.get("id") == node_id:
            return (node.get("inputs") or {}).get("processorKey")
    return None


def _declared_processor_keys() -> set[str]:
    keys = set()
    for path in RESOURCES.rglob("*.json"):
        try:
            resource = json.loads(path.read_text(encoding="utf-8")).get("resource") or {}
        except (OSError, ValueError, AttributeError):
            continue
        if str(resource.get("kind", "")).lower() == "idpprocessor" and resource.get("key"):
            keys.add(str(resource["key"]).lower())
    return keys


def main() -> int:
    flow = json.loads(FLOW.read_text(encoding="utf-8"))
    key = _processor_key(flow, TARGET)
    if not key:
        print(f"OK: {TARGET} has no processorKey")
        return 0
    if key == _processor_key(flow, SOURCE):
        print(f"FAIL: {TARGET} carries {SOURCE}'s processorKey {key}", file=sys.stderr)
        return 1
    if str(key).lower() not in _declared_processor_keys():
        print(f"FAIL: {TARGET}'s processorKey {key} is named by no idpProcessor resource under {RESOURCES}", file=sys.stderr)
        return 1
    print(f"OK: {TARGET} has its own processor {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
