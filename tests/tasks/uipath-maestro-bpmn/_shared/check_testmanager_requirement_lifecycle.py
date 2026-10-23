#!/usr/bin/env python3
"""TestManager Requirement lifecycle (BPMN): connector node presence and coverage.

Assertion map (Flow -> BPMN):
  F criterion 2   flow_contains 'uipath-uipath-testmanager.'                  -> connector_requests() non-empty (main, no --all-ops)
  F criterion 3   validate_flow.py (flow validates)                          -> `uip maestro bpmn validate` (grader YAML criterion 3)
  F criterion 4   flow_contains <6 node types, one per op>                    -> one classified node per op (main, --all-ops)
  I               locate/parse the .bpmn                                     -> parse_bpmn()
  T               objectName+method or method+path classification            -> OPERATIONS / require_operations()
  T               GETBYID/GET equivalence for "get the requirement"          -> OPERATIONS methods set {"getbyid", "get"}
  T               N distinct node types -> N distinct nodes                  -> objectName+method or method+path is unique per op
  DROPPED         require_no_private_connector_values   (not in Flow)
  DROPPED         require_sequence_integrity            (not in Flow)
  DROPPED         require_di_for_visible_elements        (not in Flow)

Ported from Flow `connector_features/testmanager_requirement_lifecycle.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per Requirement-lifecycle operation -- create, get, update,
delete, assign test cases, get assigned test cases), translated from a JSON
``.flow`` substring search to an XML walk over the sendTasks that call the
Test Manager connector (``bpmn_check.connector_requests``), in either shape:

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
distinguishes operations, by ``objectName`` + ``method``, since
``Requirement`` is the objectName for four of the six graded operations
(create/get/update/delete) and only ``method`` tells them apart. An HTTP node
is matched by ``method`` + the operation's IS enrichment path
(``registry get`` without ``--input-details``), every placeholder filled
(``/v2/{ProjectId}/requirements/{}`` does not count).

    create                   Requirement                         POST     /v2/{ProjectId}/requirements
    get                      Requirement                         GETBYID  /v2/{ProjectId}/requirements/{id}
    update                   Requirement                         PATCH    /v2/{ProjectId}/requirements/{id}
    delete                   Requirement                         DELETE   /v2/{ProjectId}/requirements/{id}
    assign test cases        AssignTestCasesToRequirement        POST     /v2/{ProjectId}/requirements/{Id}/assigntestcases
    get assigned test cases  GetAssignedTestCasesForRequirement  GET      /v2/{ProjectId}/requirements/{Id}/assignedtestcaseids

Tolerance: because the skill may normalise a "get one" node's method
spelling, this checker treats GETBYID and GET as equivalent for the single
"get the requirement" operation only. Nothing else is normalised -- a
mismatched method on any other operation fails. An HTTP request takes the
HTTP verb only: GET, never GETBYID.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_requirement_lifecycle.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_requirement_lifecycle.py --all-ops

With no arguments: asserts at least one sendTask calls the Test Manager
connector, in either shape.
With ``--all-ops``: additionally asserts all six Requirement-lifecycle
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
    ConnectorOperation("create a requirement", "Requirement", {"post"},
                       "/v2/{ProjectId}/requirements"),
    ConnectorOperation("get the requirement", "Requirement", {"getbyid", "get"},
                       "/v2/{ProjectId}/requirements/{id}"),
    ConnectorOperation("update the requirement", "Requirement", {"patch"},
                       "/v2/{ProjectId}/requirements/{id}"),
    ConnectorOperation("delete the requirement", "Requirement", {"delete"},
                       "/v2/{ProjectId}/requirements/{id}"),
    ConnectorOperation("assign test cases to the requirement",
                       "AssignTestCasesToRequirement", {"post"},
                       "/v2/{ProjectId}/requirements/{Id}/assigntestcases"),
    ConnectorOperation("get the assigned test cases for the requirement",
                       "GetAssignedTestCasesForRequirement", {"get"},
                       "/v2/{ProjectId}/requirements/{Id}/assignedtestcaseids"),
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

    require_operations(requests, OPERATIONS, "Requirement lifecycle")
    print("OK: all six Requirement lifecycle operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
