#!/usr/bin/env python3
"""Helper for copy_taxonomy.yaml: Extract Credit Note will run the taxonomy it was given.

At run time an Extract document node extracts with the processor its
inputs.processorKey names, and that processor holds its own copy of the
taxonomy. Copying the taxonomy onto the node therefore counts only if the
processor behind the node carries it too.

- No processorKey: passes. The CLI did not provision one on `nodes schema set`;
  the Studio Web save provisions it from the node's taxonomy.
- Extract Invoice's processorKey: fails. Credit Note would run Invoice's processor.
- A key no idpProcessor resource in the solution declares: fails. It points at
  nothing, so it was synthesised.
- A resource whose prompt or output schema differs from the node's: fails.
  Credit Note would extract with that stale taxonomy, not the copy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

FLOW = Path("BillingDocs", "BillingDocs", "BillingDocs.flow")
RESOURCES = Path("BillingDocs", "resources")
TARGET, SOURCE = "extractCreditNote1", "extractInvoice1"


def _inputs(flow: dict, node_id: str) -> dict:
    for node in flow.get("nodes") or []:
        if node.get("id") == node_id:
            return node.get("inputs") or {}
    raise SystemExit(f"FAIL: no node {node_id} in {FLOW}")


def _find_processor(key: str) -> tuple[Path, dict] | None:
    for path in sorted(RESOURCES.rglob("*.json")):
        try:
            resource = json.loads(path.read_text(encoding="utf-8")).get("resource") or {}
        except (OSError, ValueError, AttributeError):
            continue
        if str(resource.get("kind", "")).lower() == "idpprocessor" and str(resource.get("key", "")).lower() == key.lower():
            return path, resource
    return None


def _as_json(value: object) -> object:
    return json.loads(value) if isinstance(value, str) else value


def main() -> int:
    flow = json.loads(FLOW.read_text(encoding="utf-8"))
    target = _inputs(flow, TARGET)
    key = target.get("processorKey")
    if not key:
        print(f"OK: {TARGET} has no processorKey; the Studio Web save provisions it from the node's taxonomy")
        return 0
    if key == _inputs(flow, SOURCE).get("processorKey"):
        print(f"FAIL: {TARGET} carries {SOURCE}'s processorKey {key}, so it would run {SOURCE}'s processor", file=sys.stderr)
        return 1
    found = _find_processor(key)
    if found is None:
        print(f"FAIL: {TARGET}'s processorKey {key} is declared by no idpProcessor resource under {RESOURCES}", file=sys.stderr)
        return 1
    path, resource = found
    spec = resource.get("spec") or {}
    taxonomy = target.get("schemaDocument") or {}
    stale = [
        name
        for name, held, given in (
            ("prompt", spec.get("prompt"), taxonomy.get("prompt")),
            ("outputSchema", _as_json(spec.get("outputSchema")), taxonomy.get("outputSchema")),
        )
        if held != given
    ]
    if stale:
        print(f"FAIL: processor {path} holds a different {' and '.join(stale)} than {TARGET}, so {TARGET} would extract with it", file=sys.stderr)
        return 1
    print(f"OK: {TARGET} runs its own processor {key}, which holds the copied taxonomy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
