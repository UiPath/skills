#!/usr/bin/env python3
"""TestManager TestCase lifecycle (BPMN): connector node presence and coverage.

Ported from Flow `connector_features/testmanager_testcase_lifecycle.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per TestCase-lifecycle operation -- create, get, update,
delete, execute), translated from a JSON ``.flow`` substring search to an XML
walk over the registry-driven ``Intsvc.ActivityExecution`` connector shell
(see skills/uipath-maestro-bpmn/references/registry-workflow.md §3).

Flow distinguished operations by node ``type``
(``uipath.connector.uipath-uipath-testmanager.<op>``). BPMN's registry-driven
shell carries no per-operation node type -- every Test Manager node is the
same ``Intsvc.ActivityExecution`` wrapper with a shared ``connectorKey``.
Operations are distinguished the way the Test Manager activity catalog
(``uip is activities list uipath-uipath-testmanager --output json``) itself
distinguishes them: by ``objectName`` + ``method``, since ``TestCase`` is the
objectName for four of the five graded operations (create/get/update/delete)
and only ``method`` tells them apart:

    create  -> objectName TestCase,         method POST
    get     -> objectName TestCase,         method GETBYID (or GET; see below)
    update  -> objectName TestCase,         method PATCH
    delete  -> objectName TestCase,         method DELETE
    execute -> objectName ExecuteTestCases, method POST

Tolerance: because the skill may normalise a "get one" node's method
spelling, this checker treats GETBYID and GET as equivalent for the single
"get the test case" operation only. Nothing else is normalised -- a
mismatched method on any other operation fails.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_testcase_lifecycle.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_testcase_lifecycle.py --all-ops

With no arguments: asserts at least one Test Manager ``Intsvc.ActivityExecution``
sendTask exists (connectorKey ``uipath-uipath-testmanager``).
With ``--all-ops``: additionally asserts all five TestCase-lifecycle
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
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

CONNECTOR_KEY = "uipath-uipath-testmanager"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

# (label, objectName, {acceptable method values, lowercased})
OPERATIONS = [
    ("create a test case", "TestCase", {"post"}),
    ("get the test case", "TestCase", {"getbyid", "get"}),
    ("update the test case", "TestCase", {"patch"}),
    ("delete the test case", "TestCase", {"delete"}),
    ("execute the test case(s)", "ExecuteTestCases", {"post"}),
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
        fail("missing TestCase lifecycle connector node(s):\n  " + "\n  ".join(missing))

    require_no_private_connector_values(root)
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print("OK: all five TestCase lifecycle operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
