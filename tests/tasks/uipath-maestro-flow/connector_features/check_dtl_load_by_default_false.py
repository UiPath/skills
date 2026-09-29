#!/usr/bin/env python3
"""Verify a WooCommerce product-listing node exercises the DTL
loadByDefault=false feature: its `attribute_term` dropdown (values load only on
interaction) is actually configured on a node bound to a real connection.

Asserted on the emitted `.flow`, which both authoring loops produce with the
same shape (`inputs.detail.connectionId` + `inputs.detail.queryParameters`):

  * a `uipath.connector.uipath-automattic-woocommerce.*` node whose
    `inputs.detail.queryParameters.attribute_term` is set;
  * that value is a term id (integer) or a runtime expression (`=`-prefixed),
    never free text — a prose placeholder is what an unresolved lookup looks like;
  * `inputs.detail.connectionId` is a non-stub connection id.

Why: without these, an unconfigured node (no `inputs.detail`) passes
`flow validate` with only a warning, so "file exists + mentions the connector +
validates" scored 1.0 on a build that never touched the feature under test.

Usage:
    check_dtl_load_by_default_false.py [flow_glob]

flow_glob defaults to '**/DTLLoadByDefaultFalseTest*.flow'; falls back to any
.flow.

Exit codes:
  0 — node found, bound, attribute_term configured
  1 — assertion failed (message printed)
"""

from __future__ import annotations

import glob
import json
import re
import sys

NODE_PREFIX = "uipath.connector.uipath-automattic-woocommerce."
FIELD = "attribute_term"
STUB_CONNECTION = re.compile(r"^0{8}-0{4}-0{4}-0{4}-0{11}\d$")
GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _woo_nodes(pattern: str) -> list[tuple[str, dict]]:
    candidates = glob.glob(pattern, recursive=True) or glob.glob("**/*.flow", recursive=True)
    if not candidates:
        _fail("no .flow file found in the workspace")
    found: list[tuple[str, dict]] = []
    for path in candidates:
        try:
            with open(path, encoding="utf-8") as handle:
                flow = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        for node in flow.get("nodes", []):
            if str(node.get("type", "")).startswith(NODE_PREFIX):
                found.append((path, node))
    if not found:
        _fail(f"no {NODE_PREFIX}* node in any .flow matching '{pattern}' (or '**/*.flow')")
    return found


def _is_configured_value(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    return bool(re.fullmatch(r"\d+", text)) or text.startswith("=")


def main() -> None:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "**/DTLLoadByDefaultFalseTest*.flow"
    problems: list[str] = []
    for path, node in _woo_nodes(pattern):
        where = f"node '{node.get('id')}' in {path}"
        detail = (node.get("inputs") or {}).get("detail")
        if not isinstance(detail, dict):
            problems.append(f"{where} has no inputs.detail — the connector was never configured")
            continue
        value = (detail.get("queryParameters") or {}).get(FIELD)
        if value in (None, ""):
            problems.append(f"{where} has no inputs.detail.queryParameters.{FIELD}")
            continue
        if not _is_configured_value(value):
            problems.append(
                f"{where} sets {FIELD}={value!r} — expected a term id or a runtime "
                "expression, not free text (an unresolved lookup)"
            )
            continue
        connection = str(detail.get("connectionId") or "")
        if not GUID.match(connection) or STUB_CONNECTION.match(connection):
            problems.append(
                f"{where} is not bound to a real connection (connectionId={connection!r})"
            )
            continue
        print(f"OK: {where} sets {FIELD}={value!r} on connection {connection}")
        return
    _fail("; ".join(problems))


if __name__ == "__main__":
    main()
