#!/usr/bin/env python3
"""TestManager execution/results group (BPMN): connector node presence and coverage.

Ported from Flow `connector_features/testmanager_execution_results.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per execution/results operation -- get a test execution,
delete a test execution, get the test case logs of a test execution, get a
test case log, get robot logs, get assertions, download an assertion, get
test steps, get test step logs), translated from a JSON ``.flow`` substring
search to an XML walk over the sendTasks that call the Test Manager
connector (``bpmn_check.connector_requests``), in either shape:

- ``Intsvc.ActivityExecution`` with ``connectorKey`` ``uipath-uipath-testmanager``
  (see skills/uipath-maestro-bpmn/references/registry-workflow.md §3), except
  on object ``http-request``.
- connector-mode ``Intsvc.UnifiedHttpRequest`` with ``targetConnector``
  ``uipath-uipath-testmanager``. A manual-mode request, or one through
  another connector, does not count.

Flow distinguished operations by node ``type``
(``uipath.connector.uipath-uipath-testmanager.<op>``). BPMN carries no
per-operation node type. An ``Intsvc.ActivityExecution`` node is matched the
way the Test Manager activity catalog
(``uip is activities list uipath-uipath-testmanager --output json``)
distinguishes operations, by ``objectName`` + ``method``. An HTTP node is
matched by ``method`` + the operation's IS enrichment path
(``registry get`` without ``--input-details``), every placeholder filled
(``/v2/{projectId}/teststeplogs`` does not count).

    get a test execution                        TestExecution                   GETBYID  /v2/{projectId}/testexecutions/{id}
    delete a test execution                     TestExecution                   DELETE   /v2/{projectId}/testexecutions/{id}
    get the test case logs of a test execution  GetTestCaseLogsOfTestExecution  GET      /v2/{projectId}/testcaselogs/testexecution/{testExecutionId}/paged
    get a test case log                         TestCaseLog                     GETBYID  /v2/{projectId}/testcaselogs/{id}
    get robot logs                              GetRobotLogs                    GET      /v2/{projectId}/orchestrator/testexecution/{id}/robotlogs/paged
    get assertions                              GetAssertions                   GET      /v2/{projectId}/testcaselogartifacts/{id}/assertions
    download an assertion                       DownloadAssertion               GETBYID  /v2/{projectId}/testcaselogartifacts/{id}/assertions/{assertionId}/downloadscreenshot
    get test steps                              GetTestSteps                    GET      /v2/{ProjectId}/teststeps/testcase/{Id}
    get test step logs                          GetTestStepLogs                 GET      /v2/{projectId}/teststeplogs

Tolerance: because the skill may normalise a "get one by id" node's method
spelling, this checker treats GETBYID and GET as equivalent for the three
get-one-by-id operations only (get a test execution, get a test case log,
download an assertion) -- the same tolerance the sibling
`check_testmanager_testcase_lifecycle.py` applies to its analogous "get the
test case" operation. Nothing else is normalised -- a mismatched method on
any other operation fails. An HTTP request takes the HTTP verb only: GET,
never GETBYID.

Assertion map (Flow -> BPMN):
  F criterion 2   flow_contains 'uipath-uipath-testmanager.'            -> connector_requests() non-empty (main(), no --all-ops)
  F criterion 4   flow_contains <9 node types>                          -> one classified node per op (main(), --all-ops)
  I               locate/parse .bpmn                                    -> parse_bpmn()
  T               objectName+method or method+path classification       -> OPERATIONS / require_operations()
  T               GETBYID/GET equivalence for get-one-by-id operations   -> OPERATIONS methods set
  DROPPED         require_no_private_connector_values (not in Flow)
  DROPPED         require_sequence_integrity (not in Flow; Flow checked no ordering)
  DROPPED         require_di_for_visible_elements (not in Flow; validate criterion covers structure)
  DROPPED         `claimed` node-exclusion set (get/delete on TestExecution
                  are distinguished by disjoint method sets, and the other
                  path patterns are end-anchored and disjoint, so no node
                  matches two operations)

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_execution_results.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_execution_results.py --all-ops

With no arguments: asserts at least one sendTask calls the Test Manager
connector, in either shape.
With ``--all-ops``: additionally asserts all nine execution/results
operations are present, each as its own distinct sendTask.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    ConnectorOperation,
    connector_requests,
    fail,
    parse_bpmn,
    require_operations,
)

CONNECTOR_KEY = "uipath-uipath-testmanager"
OPERATIONS = [
    ConnectorOperation("get a test execution", "TestExecution", {"getbyid", "get"},
                       "/v2/{projectId}/testexecutions/{id}"),
    ConnectorOperation("delete a test execution", "TestExecution", {"delete"},
                       "/v2/{projectId}/testexecutions/{id}"),
    ConnectorOperation("get the test case logs of a test execution",
                       "GetTestCaseLogsOfTestExecution", {"get"},
                       "/v2/{projectId}/testcaselogs/testexecution/{testExecutionId}/paged"),
    ConnectorOperation("get a test case log", "TestCaseLog", {"getbyid", "get"},
                       "/v2/{projectId}/testcaselogs/{id}"),
    ConnectorOperation("get robot logs", "GetRobotLogs", {"get"},
                       "/v2/{projectId}/orchestrator/testexecution/{id}/robotlogs/paged"),
    ConnectorOperation("get assertions", "GetAssertions", {"get"},
                       "/v2/{projectId}/testcaselogartifacts/{id}/assertions"),
    ConnectorOperation("download an assertion", "DownloadAssertion", {"getbyid", "get"},
                       "/v2/{projectId}/testcaselogartifacts/{id}/assertions/{assertionId}/downloadscreenshot"),
    ConnectorOperation("get test steps", "GetTestSteps", {"get"},
                       "/v2/{ProjectId}/teststeps/testcase/{Id}"),
    ConnectorOperation("get test step logs", "GetTestStepLogs", {"get"},
                       "/v2/{projectId}/teststeplogs"),
]


def main() -> None:
    all_ops = "--all-ops" in sys.argv[1:]

    path, root = parse_bpmn()
    requests = list(connector_requests(root, CONNECTOR_KEY))
    if not requests:
        fail(
            "no bpmn:sendTask calls the Test Manager connector: expected "
            f"Intsvc.ActivityExecution with connectorKey {CONNECTOR_KEY!r}, or a "
            "connector-mode Intsvc.UnifiedHttpRequest with targetConnector "
            f"{CONNECTOR_KEY!r}"
        )
    print(f"OK: {len(requests)} {CONNECTOR_KEY} sendTask(s) present in {path}")

    if not all_ops:
        return

    require_operations(requests, OPERATIONS, "execution/results")
    print("OK: all nine execution/results operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
