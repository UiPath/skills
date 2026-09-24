#!/usr/bin/env python3
"""TestManager generic record operations (BPMN): connector node presence and coverage.

Assertion map (Flow -> BPMN):
  F criterion 2   flow_contains 'uipath-uipath-testmanager.'                  -> connector_tasks(root) non-empty (main, no --all-ops)
  F criterion 3   validate_flow.py (flow validates)                          -> `uip maestro bpmn validate` (grader YAML criterion 3)
  F criterion 4   flow_contains <5 node types, one per op>                    -> one classified node per op, distinct nodes (main, --all-ops)
  I               locate/parse the .bpmn                                     -> parse_bpmn()
  T               curated generic-record classification (operation + method)  -> matches_operation() / OPERATIONS
  T               N distinct node types -> N distinct nodes                   -> used_ids tracking in main()
  DROPPED         require_no_private_connector_values   (not in Flow)
  DROPPED         require_sequence_integrity            (not in Flow)
  DROPPED         require_di_for_visible_elements        (not in Flow)
  DROPPED         non-empty objectName requirement        (not in Flow)

Ported from Flow `connector_features/testmanager_generic_records.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per generic-record operation -- insert, get, update, delete,
list), translated from a JSON ``.flow`` substring search to an XML walk over
the registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3).

Flow distinguished operations by node ``type``
(``uipath.connector.uipath-uipath-testmanager.insert-record`` etc.). BPMN's
registry-driven shell carries no per-operation node type -- every Test
Manager node is the same ``Intsvc.ActivityExecution`` wrapper with a shared
``connectorKey``. Operations are distinguished by the registry's own
``operation`` context field, exactly as the catalog names them:

    insert a record -> operation Create,   method fallback POST
    get a record    -> operation Retrieve, method fallback GETBYID
    update a record -> operation Update,   method fallback PATCH or PUT
    delete a record -> operation Delete,   method fallback DELETE
    list records     -> operation List,     method fallback GET

``operation`` is matched case-insensitively. The HTTP ``method`` fallback is
used only when a node has no ``operation`` value at all -- when ``operation``
is present it alone decides the match, so a node is never scored against the
wrong criterion because of an incidental method value.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_generic_records.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_generic_records.py --all-ops

With no arguments: asserts at least one Test Manager ``Intsvc.ActivityExecution``
sendTask exists (connectorKey ``uipath-uipath-testmanager``).
With ``--all-ops``: additionally asserts all five generic-record operations
are present, each as its own distinct sendTask.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    attr,
    context_value,
    elements,
    fail,
    has_type,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-testmanager"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

# (label, operation value (case-insensitive), {method fallback values, lowercased})
# Fallback methods only apply when a node carries no `operation` value at all.
OPERATIONS = [
    ("insert a record", "create", {"post"}),
    ("get a record", "retrieve", {"getbyid"}),
    ("update a record", "update", {"patch", "put"}),
    ("delete a record", "delete", {"delete"}),
    ("list records", "list", {"get"}),
]


def connector_tasks(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_type(task, ACTIVITY_TYPE) and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def matches_operation(task: ET.Element, operation_value: str, methods: set[str]) -> bool:
    operation = context_value(task, "operation").lower()
    if operation:
        return operation == operation_value
    return context_value(task, "method").lower() in methods


def main() -> None:
    all_ops = "--all-ops" in sys.argv[1:]

    path, root = parse_bpmn()
    tasks = connector_tasks(root)
    if not tasks:
        fail(
            f"no bpmn:sendTask carrying {ACTIVITY_TYPE} for connector key "
            f"{CONNECTOR_KEY!r}"
        )
    print(f"OK: {len(tasks)} {CONNECTOR_KEY} sendTask(s) present in {path}")

    if not all_ops:
        return

    missing: list[str] = []
    used_ids: set[str] = set()
    for label, operation_value, methods in OPERATIONS:
        match = next(
            (
                t
                for t in tasks
                if attr(t, "id") not in used_ids
                and matches_operation(t, operation_value, methods)
            ),
            None,
        )
        if match is None:
            missing.append(
                f"{label} (operation={operation_value!r} or method in {sorted(methods)})"
            )
        else:
            used_ids.add(attr(match, "id"))
            print(
                f"OK: {label} -> {attr(match, 'id') or '?'} "
                f"(objectName={context_value(match, 'objectName')!r}, "
                f"operation={context_value(match, 'operation')!r}, "
                f"method={context_value(match, 'method')!r})"
            )

    if missing:
        fail("missing generic record connector node(s):\n  " + "\n  ".join(missing))

    print("OK: all five generic record operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
