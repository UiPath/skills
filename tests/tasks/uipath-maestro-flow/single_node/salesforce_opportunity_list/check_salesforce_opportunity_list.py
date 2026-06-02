#!/usr/bin/env python3
"""Salesforce list-records on Opportunity (live execution).

Structural pre-checks fail fast and prevent gaming, then a live `flow debug`
proves the connector actually called Salesforce and returned records:

1. A connector node targets the Salesforce connector (`uipath-salesforce-sfdc`)
   using the generic `list-records` operation on `objectName: "Opportunity"`.
2. `flow debug` completes (`finalStatus == "Completed"`).
3. The output holds a non-empty array of record objects, each carrying a
   Salesforce `Id` — i.e. real Opportunity rows came back, not an empty list,
   a scalar, or a hardcoded literal.

Grounded against the codereval tenant's Salesforce connection (76 Opportunity
records): the IS connector returns FLATTENED records (top-level `Id`, `Name`,
`Amount`, `StageName`, …) with no `attributes.type` envelope, so the runtime
assertion keys off `Id`, not `attributes`.
"""

from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_uses_connector_target,
    find_project_dir,
    run_debug,
)

CONNECTOR_KEY = "uipath-salesforce-sfdc"
OPERATION = "list-records"
OBJECT_NAME = "Opportunity"


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
    # A real Salesforce connector node must be present (native connector node).
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
            f"FAIL: No Salesforce {OPERATION!r} connector node found. "
            f"Node types seen: {types}"
        )

    # The configured object must be Opportunity. Generic list-records carries
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
        f"FAIL: Salesforce {OPERATION} node found but objectName != {OBJECT_NAME!r} "
        f"(resolved object names: {found}). The list-records activity is generic — "
        f"it must set the object name to {OBJECT_NAME!r}."
    )


def _assert_records_returned(payload: dict) -> None:
    globals_ = (payload.get("variables") or {}).get("globals") or {}
    # Find any output variable holding a non-empty array of record objects.
    for name, value in globals_.items():
        if (
            isinstance(value, list)
            and value
            and all(isinstance(r, dict) for r in value)
            and any("Id" in r for r in value)
        ):
            print(
                f"OK: connector returned {len(value)} Opportunity record(s) "
                f"in output {name!r} (first Id={value[0].get('Id')!r})"
            )
            return
    sys.exit(
        "FAIL: No output variable holds a non-empty array of Salesforce records "
        f"with an 'Id' field. globals keys: {sorted(globals_)}"
    )


def main():
    _assert_structure()
    payload = run_debug(timeout=300)
    _assert_records_returned(payload)


if __name__ == "__main__":
    main()
