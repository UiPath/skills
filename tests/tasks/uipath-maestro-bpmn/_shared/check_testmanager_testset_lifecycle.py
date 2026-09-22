#!/usr/bin/env python3
"""TestManager TestSet lifecycle (BPMN): connector node presence and coverage.

Assertion map (Flow -> BPMN):
  F criterion 2   flow_contains 'uipath-uipath-testmanager.'                  -> connector_tasks(root) non-empty (main, no --all-ops)
  F criterion 3   validate_flow.py (flow validates)                          -> `uip maestro bpmn validate` (grader YAML criterion 3)
  F criterion 4   flow_contains <7 node types, one per op>                    -> one classified node per op (main, --all-ops)
  I               locate/parse the .bpmn                                     -> parse_bpmn()
  T               curated objectName+method classification                   -> OPERATIONS / match loop
  T               GETBYID/GET equivalence for "get the test set"             -> OPERATIONS methods set {"getbyid", "get"}
  T               N distinct node types -> N distinct nodes                  -> used tracking in main()
  DROPPED         require_no_private_connector_values   (not in Flow)
  DROPPED         require_sequence_integrity            (not in Flow)
  DROPPED         require_di_for_visible_elements        (not in Flow)

Ported from Flow `connector_features/testmanager_testset_lifecycle.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per TestSet-lifecycle operation -- create, get, update,
delete, assign test cases, list assigned test cases, execute), translated
from a JSON ``.flow`` substring search to an XML walk over the
registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3).

Flow distinguished operations by node ``type``
(``uipath.connector.uipath-uipath-testmanager.<op>``). BPMN's registry-driven
shell carries no per-operation node type -- every Test Manager node is the
same ``Intsvc.ActivityExecution`` wrapper with a shared ``connectorKey``.
Operations are distinguished the way the Test Manager activity catalog
(``uip is activities list uipath-uipath-testmanager --output json``) itself
distinguishes them: by ``objectName`` + ``method``, since ``TestSet`` is the
objectName for four of the seven graded operations (create/get/update/delete)
and only ``method`` tells them apart; the remaining three operations each
have their own unique objectName:

    create  -> objectName TestSet,                      method POST
    get     -> objectName TestSet,                       method GETBYID (or GET; see below)
    update  -> objectName TestSet,                        method PATCH
    delete  -> objectName TestSet,                        method DELETE
    assign  -> objectName AssignTestCasesToTestSet,        method POST
    list    -> objectName GetAssignedTestCasesForTestSet,  method GET
    execute -> objectName ExecuteTestSet,                  method POST

Tolerance: because the skill may normalise a "get one" node's method
spelling, this checker treats GETBYID and GET as equivalent for the single
"get the test set" operation only. Nothing else is normalised -- a
mismatched method on any other operation fails.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_testset_lifecycle.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_testset_lifecycle.py --all-ops

With no arguments: asserts at least one Test Manager ``Intsvc.ActivityExecution``
sendTask exists (connectorKey ``uipath-uipath-testmanager``).
With ``--all-ops``: additionally asserts all seven TestSet-lifecycle
operations are present, each as its own distinct sendTask.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    context_value,
    elements,
    fail,
    has_type,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-testmanager"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

# (label, objectName, {acceptable method values, lowercased})
OPERATIONS = [
    ("create a test set", "TestSet", {"post"}),
    ("get the test set", "TestSet", {"getbyid", "get"}),
    ("update the test set", "TestSet", {"patch"}),
    ("delete the test set", "TestSet", {"delete"}),
    ("assign test cases to the test set", "AssignTestCasesToTestSet", {"post"}),
    ("list the test cases assigned to the test set", "GetAssignedTestCasesForTestSet", {"get"}),
    ("execute (run) the test set", "ExecuteTestSet", {"post"}),
]


def connector_tasks(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_type(task, ACTIVITY_TYPE) and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


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
    used: set[str] = set()
    for label, object_name, methods in OPERATIONS:
        match = next(
            (
                t
                for t in tasks
                if t.attrib.get("id", "?") not in used
                and context_value(t, "objectName") == object_name
                and context_value(t, "method").lower() in methods
            ),
            None,
        )
        if match is None:
            missing.append(f"{label} (objectName={object_name!r}, method in {sorted(methods)})")
        else:
            used.add(match.attrib.get("id", "?"))
            print(f"OK: {label} -> {match.attrib.get('id', '?')} "
                  f"(objectName={object_name!r}, method={context_value(match, 'method')!r})")

    if missing:
        fail("missing TestSet lifecycle connector node(s):\n  " + "\n  ".join(missing))

    print("OK: all seven TestSet lifecycle operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
