#!/usr/bin/env python3
"""TestManager execution/results group (BPMN): connector node presence and coverage.

Ported from Flow `connector_features/testmanager_execution_results.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per execution/results operation -- get a test execution,
delete a test execution, get the test case logs of a test execution, get a
test case log, get robot logs, get assertions, download an assertion, get
test steps, get test step logs), translated from a JSON ``.flow`` substring
search to an XML walk over the registry-driven ``Intsvc.ActivityExecution``
connector shell (see skills/uipath-maestro-bpmn/references/registry-workflow.md
§3), following the same node-classification pattern as the sibling port
`check_testmanager_testcase_lifecycle.py`.

Flow distinguished operations by node ``type``
(``uipath.connector.uipath-uipath-testmanager.<op>``). BPMN's registry-driven
shell carries no per-operation node type -- every Test Manager node is the
same ``Intsvc.ActivityExecution`` wrapper with a shared ``connectorKey``.
Operations are distinguished the way the Test Manager activity catalog
(``uip is activities list uipath-uipath-testmanager --output json``) itself
distinguishes them: by ``objectName`` + ``method``, since ``TestExecution``
is the objectName shared by the "get a test execution" and "delete a test
execution" operations and only ``method`` tells them apart:

    get a test execution                       -> objectName TestExecution,                      method GETBYID (or GET; see below)
    delete a test execution                     -> objectName TestExecution,                      method DELETE
    get the test case logs of a test execution  -> objectName GetTestCaseLogsOfTestExecution,      method GET
    get a test case log                         -> objectName TestCaseLog,                        method GETBYID (or GET; see below)
    get robot logs                              -> objectName GetRobotLogs,                        method GET
    get assertions                               -> objectName GetAssertions,                       method GET
    download an assertion                       -> objectName DownloadAssertion,                    method GETBYID (or GET; see below)
    get test steps                              -> objectName GetTestSteps,                         method GET
    get test step logs                          -> objectName GetTestStepLogs,                      method GET

Tolerance: because the skill may normalise a "get one by id" node's method
spelling, this checker treats GETBYID and GET as equivalent for the three
get-one-by-id operations only (get a test execution, get a test case log,
download an assertion) -- the same tolerance the sibling
`check_testmanager_testcase_lifecycle.py` applies to its analogous "get the
test case" operation. Nothing else is normalised -- a mismatched method on
any other operation fails.

Assertion map (Flow -> BPMN):
  F criterion 2   flow_contains 'uipath-uipath-testmanager.'            -> connector_tasks() non-empty (main(), no --all-ops)
  F criterion 4   flow_contains <9 node types>                          -> one classified node per op (main(), --all-ops)
  I               locate/parse .bpmn                                    -> parse_bpmn()
  T               objectName+method classification (no per-op node type)-> OPERATIONS / context_value()
  T               GETBYID/GET equivalence for get-one-by-id operations   -> OPERATIONS methods set
  DROPPED         require_no_private_connector_values (not in Flow)
  DROPPED         require_sequence_integrity (not in Flow; Flow checked no ordering)
  DROPPED         require_di_for_visible_elements (not in Flow; validate criterion covers structure)
  DROPPED         `claimed` node-exclusion set (get/delete on TestExecution
                  already distinguished by disjoint method sets -- {getbyid,get}
                  vs {delete} never overlap, so excluding a matched node from
                  later ops changes no outcome; objectName+method alone is the
                  N-distinct-node-types translation)

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_execution_results.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_execution_results.py --all-ops

With no arguments: asserts at least one Test Manager ``Intsvc.ActivityExecution``
sendTask exists (connectorKey ``uipath-uipath-testmanager``).
With ``--all-ops``: additionally asserts all nine execution/results
operations are present, each as its own distinct sendTask.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import NS, elements, fail, parse_bpmn  # noqa: E402

CONNECTOR_KEY = "uipath-uipath-testmanager"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

# (label, objectName, {acceptable method values, lowercased})
OPERATIONS = [
    ("get a test execution", "TestExecution", {"getbyid", "get"}),
    ("delete a test execution", "TestExecution", {"delete"}),
    ("get the test case logs of a test execution", "GetTestCaseLogsOfTestExecution", {"get"}),
    ("get a test case log", "TestCaseLog", {"getbyid", "get"}),
    ("get robot logs", "GetRobotLogs", {"get"}),
    ("get assertions", "GetAssertions", {"get"}),
    ("download an assertion", "DownloadAssertion", {"getbyid", "get"}),
    ("get test steps", "GetTestSteps", {"get"}),
    ("get test step logs", "GetTestStepLogs", {"get"}),
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
        fail("missing execution/results connector node(s):\n  " + "\n  ".join(missing))

    print("OK: all nine execution/results operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
