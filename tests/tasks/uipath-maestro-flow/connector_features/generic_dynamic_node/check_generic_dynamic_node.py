#!/usr/bin/env python3
"""Generic (dynamic) connector node — structural + live execution.

Validates a generic connector activity: the node type encodes only the
operation, so the object is supplied dynamically at configure time and must be
resolved + set on the node. Uses ServiceNow `list-all-records` on `acr_user` as
the concrete generic activity. Structural pre-checks fail fast and prevent
gaming, then a live `flow debug` proves the generic node actually executed:

1. A connector node targets the ServiceNow connector (`uipath-servicenow-servicenow`)
   using the generic `list-all-records` operation on `objectName: "acr_user"`.
2. `flow debug` completes (`finalStatus == "Completed"`).
3. The connector result is surfaced as an array output variable.

The `acr_user` table is empty in the codereval ServiceNow tenant, so the
list-all-records call legitimately returns `[]`. The runtime assertion therefore
checks that the connector completed and surfaced an array output (empty
allowed) — not that rows came back. When records ARE present the IS connector
returns FLATTENED records (top-level `sys_id`, …), which the check reports.
"""

from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    _get_ci,
    assert_flow_uses_connector_target,
    find_project_dir,
    run_debug,
)

CONNECTOR_KEY = "uipath-servicenow-servicenow"
OPERATION = "list-all-records"
# API object name (not the "Acr User" display name) — `node configure` stores
# the connector's case-sensitive `Name`, which for this table is `acr_user`.
OBJECT_NAME = "acr_user"


def _load_flow_nodes(project_dir: str) -> list[dict]:
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        sys.exit(f"FAIL: No .flow file found under {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    return flow.get("nodes") or []


def _detail_object_name(detail: dict) -> str | None:
    """Resolve the configured object name for a generic connector node.

    `node configure` stores it in a few places depending on CLI version: a
    top-level `inputs.detail.objectName`, or inside the serialized
    `configuration` string (`=jsonString:{...}`) at `objectName`,
    `essentialConfiguration.objectName`, or `…instanceParameters.objectName`."""
    if detail.get("objectName"):
        return detail["objectName"]
    cfg = detail.get("configuration")
    if isinstance(cfg, str):
        prefix = "=jsonString:"
        body = cfg[len(prefix):] if cfg.startswith(prefix) else cfg
        try:
            obj = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return None
        ess = obj.get("essentialConfiguration") if isinstance(obj, dict) else None
        ess = ess if isinstance(ess, dict) else {}
        params = ess.get("instanceParameters") if isinstance(ess, dict) else None
        params = params if isinstance(params, dict) else {}
        return obj.get("objectName") or ess.get("objectName") or params.get("objectName")
    return None


def _assert_structure() -> None:
    # A real ServiceNow connector node must be present (native connector node).
    assert_flow_uses_connector_target(CONNECTOR_KEY)

    nodes = _load_flow_nodes(find_project_dir())
    list_nodes = [
        n
        for n in nodes
        if CONNECTOR_KEY in str(n.get("type", "")).lower()
        and OPERATION in str(n.get("type", "")).lower()
    ]
    if not list_nodes:
        types = sorted({str(n.get("type", "")) for n in nodes})
        sys.exit(
            f"FAIL: No ServiceNow {OPERATION!r} connector node found. "
            f"Node types seen: {types}"
        )

    # The configured object must be Acr User. Generic list-all-records carries
    # objectName on inputs.detail (top-level) or inside the serialized
    # `configuration` payload — accept either.
    found = []
    for node in list_nodes:
        detail = (node.get("inputs") or {}).get("detail") or {}
        if not isinstance(detail, dict):
            continue
        name = _detail_object_name(detail)
        found.append(name)
        if name == OBJECT_NAME:
            return
    sys.exit(
        f"FAIL: ServiceNow {OPERATION} node found but objectName != {OBJECT_NAME!r} "
        f"(resolved object names: {found}). The list-all-records activity is generic — "
        f"it must set the object name to {OBJECT_NAME!r}."
    )


def _assert_array_output(payload: dict) -> None:
    """Assert the connector surfaced its result as an array output variable.

    `run_debug` already enforced `finalStatus == "Completed"`, so the connector
    call succeeded by the time we get here. The `acr_user` table is empty in the
    codereval ServiceNow tenant, so the list-all-records call legitimately
    returns `[]` — assert an array-typed output exists rather than requiring it
    to be non-empty. When records ARE present they carry a `sys_id`, so report
    that to keep the check meaningful if the table is ever populated.

    The flow debug runtime payload is PascalCase under CLI #2266
    (Variables/Globals) and camelCase otherwise; read both via _get_ci so the
    output search doesn't silently see {}.
    """
    variables = _get_ci(payload, "variables", "Variables") or {}
    globals_ = _get_ci(variables, "globals", "Globals") or {}
    for name, value in globals_.items():
        if isinstance(value, list):
            if value and all(isinstance(r, dict) for r in value) and any("sys_id" in r for r in value):
                print(
                    f"OK: connector returned {len(value)} Acr User record(s) "
                    f"in output {name!r} (first sys_id={value[0].get('sys_id')!r})"
                )
            else:
                print(
                    f"OK: connector completed and surfaced an array output {name!r} "
                    f"({len(value)} record(s)). Empty is expected — the acr_user "
                    f"table is empty in this tenant."
                )
            return
    sys.exit(
        "FAIL: No output variable holds an array — the connector result was not "
        f"surfaced as a flow output. globals keys: {sorted(globals_)}"
    )


def main():
    _assert_structure()
    payload = run_debug(timeout=300)
    _assert_array_output(payload)


if __name__ == "__main__":
    main()
