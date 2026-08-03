#!/usr/bin/env python3
"""DatabricksQuery: structural checks for the JDBC Execute-Query flow.

Checks, in order (exits non-zero with ``FAIL: ...`` on first failure):
  1. The .flow parses as JSON with nodes/edges, and wires the JDBC gateway
     connector (`uipath-uipath-jdbc`) — as a real connector node with a bound
     connection id + folder key — plus its Execute Query Synchronously operation.
     NOT a native Databricks connector, NOT a generic HTTP fallback (the special
     SDK case: Databricks SQL has no native path, it must route through JDBC).

The prompt asks for an aggregate over the `employees` table (group by department,
keep departments with two or more employees, order by average salary) — a shape
expressible only via raw SQL, not the generic record activities. The exact SQL the
agent authors is not asserted here; this checker validates only the connector
wiring described above.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path
from typing import NoReturn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_uses_connector_target,
)

FLOW_GLOB = "**/DatabricksQuery*.flow"
JDBC_KEY = "uipath-uipath-jdbc"
JDBC_OP = "execute-query-synchronously"
NATIVE_DATABRICKS_KEY = "uipath-databricks-databricks"


def _fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def _flow_path() -> str:
    flows = glob.glob(FLOW_GLOB, recursive=True)
    if not flows:
        _fail(f"no flow file matching {FLOW_GLOB}")
    return flows[0]


def _node_type(node: dict) -> str:
    return str(node.get("type") or "").lower()


def main() -> None:
    path = _flow_path()
    raw = Path(path).read_text(encoding="utf-8")

    # Structural gate: parse the flow so a malformed .flow fails fast with a clear
    # error, and so the assertions below run against node objects rather than a
    # raw substring match (which passes on a stale binding, a comment, or an
    # unrelated node).
    try:
        flow = json.loads(raw)
    except json.JSONDecodeError as e:
        _fail(f"{path} is not valid JSON: {e}")
    if "nodes" not in flow or "edges" not in flow:
        _fail("flow missing 'nodes' or 'edges'")
    nodes = flow.get("nodes") or []

    # The JDBC connector must be wired as a real connector node (or connector-mode
    # HTTP proxy) with a bound connection id + folder key — not merely mentioned
    # in the file text. assert_flow_uses_connector_target enforces the binding.
    assert_flow_uses_connector_target(JDBC_KEY)

    # The execute-query operation must be on an actual node's type/detail, not
    # anywhere in the raw file text.
    def _references_op(node: dict) -> bool:
        if JDBC_OP in _node_type(node):
            return True
        detail = (node.get("inputs") or {}).get("detail") or {}
        return isinstance(detail, dict) and JDBC_OP in json.dumps(detail).lower()

    if not any(_references_op(n) for n in nodes):
        _fail(f"no node references the {JDBC_OP} operation")
    print(f"OK: flow uses the {JDBC_KEY}.{JDBC_OP} connector with a bound connection")

    # Guard the special-SDK-case: no node may be the native Databricks connector
    # (checked on node types, so a connection name or comment containing the key
    # cannot falsely fail a legitimate JDBC flow).
    if any(NATIVE_DATABRICKS_KEY in _node_type(n) for n in nodes):
        _fail("flow references the native Databricks connector — Databricks SQL "
              "must route through the JDBC gateway, not the native key")

    print("OK: all DatabricksQuery checks passed")


if __name__ == "__main__":
    main()
