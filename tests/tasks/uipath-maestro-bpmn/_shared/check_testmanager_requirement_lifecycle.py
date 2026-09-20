#!/usr/bin/env python3
"""TestManager Requirement lifecycle (BPMN): connector node presence and coverage.

Assertion map (Flow -> BPMN):
  F criterion 2   flow_contains 'uipath-uipath-testmanager.'                  -> connector_tasks(root) non-empty (main, no --all-ops)
  F criterion 3   validate_flow.py (flow validates)                          -> `uip maestro bpmn validate` (grader YAML criterion 3)
  F criterion 4   flow_contains <6 node types, one per op>                    -> one classified node per op (main, --all-ops)
  I               locate/parse the .bpmn                                     -> parse_bpmn()
  T               curated objectName+method classification                   -> OPERATIONS / match loop
  T               GETBYID/GET equivalence for "get the requirement"          -> OPERATIONS methods set {"getbyid", "get"}
  T               N distinct node types -> N distinct nodes                  -> objectName+method combo is unique per op
  DROPPED         require_no_private_connector_values   (not in Flow)
  DROPPED         require_sequence_integrity            (not in Flow)
  DROPPED         require_di_for_visible_elements        (not in Flow)

Ported from Flow `connector_features/testmanager_requirement_lifecycle.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per Requirement-lifecycle operation -- create, get, update,
delete, assign test cases, get assigned test cases), translated from a JSON
``.flow`` substring search to an XML walk over the registry-driven
``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3).

Flow distinguished operations by node ``type``
(``uipath.connector.uipath-uipath-testmanager.<op>``). BPMN's registry-driven
shell carries no per-operation node type -- every Test Manager node is the
same ``Intsvc.ActivityExecution`` wrapper with a shared ``connectorKey``.
Operations are distinguished the way the Test Manager activity catalog
(``uip is activities list uipath-uipath-testmanager --output json``) itself
distinguishes them: by ``objectName`` + ``method``, since ``Requirement`` is
the objectName for four of the six graded operations (create/get/update/delete)
and only ``method`` tells them apart:

    create           -> objectName Requirement,                     method POST
    get              -> objectName Requirement,                     method GETBYID (or GET; see below)
    update           -> objectName Requirement,                     method PATCH
    delete           -> objectName Requirement,                     method DELETE
    assign test cases -> objectName AssignTestCasesToRequirement,   method POST
    get assigned test cases -> objectName GetAssignedTestCasesForRequirement, method GET

Tolerance: because the skill may normalise a "get one" node's method
spelling, this checker treats GETBYID and GET as equivalent for the single
"get the requirement" operation only. Nothing else is normalised -- a
mismatched method on any other operation fails.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_requirement_lifecycle.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_requirement_lifecycle.py --all-ops

With no arguments: asserts at least one Test Manager ``Intsvc.ActivityExecution``
sendTask exists (connectorKey ``uipath-uipath-testmanager``).
With ``--all-ops``: additionally asserts all six Requirement-lifecycle
operations are present, each as its own distinct sendTask.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    elements,
    fail,
    parse_bpmn,
)

CONNECTOR_KEY = "uipath-uipath-testmanager"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

# (label, objectName, {acceptable method values, lowercased})
OPERATIONS = [
    ("create a requirement", "Requirement", {"post"}),
    ("get the requirement", "Requirement", {"getbyid", "get"}),
    ("update the requirement", "Requirement", {"patch"}),
    ("delete the requirement", "Requirement", {"delete"}),
    ("assign test cases to the requirement", "AssignTestCasesToRequirement", {"post"}),
    ("get the assigned test cases for the requirement", "GetAssignedTestCasesForRequirement", {"get"}),
]


def has_type(el: ET.Element, token: str) -> bool:
    return token in ET.tostring(el, encoding="unicode")


def context_inputs(task: ET.Element) -> list[ET.Element]:
    return task.findall(".//uipath:input", NS)


def context_value(task: ET.Element, name: str) -> str:
    for inp in context_inputs(task):
        if inp.attrib.get("name") == name:
            return (inp.attrib.get("value") or inp.text or "").strip()
    return ""


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
    for label, object_name, methods in OPERATIONS:
        match = next(
            (
                t
                for t in tasks
                if context_value(t, "objectName") == object_name
                and context_value(t, "method").lower() in methods
            ),
            None,
        )
        if match is None:
            missing.append(f"{label} (objectName={object_name!r}, method in {sorted(methods)})")
        else:
            print(f"OK: {label} -> {match.attrib.get('id', '?')} "
                  f"(objectName={object_name!r}, method={context_value(match, 'method')!r})")

    if missing:
        fail("missing Requirement lifecycle connector node(s):\n  " + "\n  ".join(missing))

    print("OK: all six Requirement lifecycle operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
