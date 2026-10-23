#!/usr/bin/env python3
"""TestManager generic record operations (BPMN): connector node presence and coverage.

Assertion map (Flow -> BPMN):
  F criterion 2   flow_contains 'uipath-uipath-testmanager.'                  -> connector_requests() non-empty (main, no --all-ops)
  F criterion 3   validate_flow.py (flow validates)                          -> `uip maestro bpmn validate` (grader YAML criterion 3)
  F criterion 4   flow_contains <5 node types, one per op>                    -> one classified node per op, distinct nodes (main, --all-ops)
  I               locate/parse the .bpmn                                     -> parse_bpmn()
  T               generic-record classification (any catalog object)         -> OPERATIONS / require_operations()
  T               N distinct node types -> N distinct nodes                   -> require_operations() assigns one node per op
  DROPPED         require_no_private_connector_values   (not in Flow)
  DROPPED         require_sequence_integrity            (not in Flow)
  DROPPED         require_di_for_visible_elements        (not in Flow)
  DROPPED         non-empty objectName requirement        (not in Flow)

Ported from Flow `connector_features/testmanager_generic_records.yaml`'s
``flow_contains.py`` substring checks: same scenario (one Test Manager
connector node per generic-record operation -- insert, get, update, delete,
list), translated from a JSON ``.flow`` substring search to an XML walk over
the sendTasks that call the Test Manager connector
(``bpmn_check.connector_requests``), in either shape:

- ``Intsvc.ActivityExecution`` with ``connectorKey`` ``uipath-uipath-testmanager``
  (see skills/uipath-maestro-bpmn/references/registry-workflow.md §3), except
  on object ``http-request``.
- connector-mode ``Intsvc.UnifiedHttpRequest`` with ``targetConnector``
  ``uipath-uipath-testmanager``. A manual-mode request, or one through
  another connector, does not count.

Flow distinguished operations by node ``type``
(``uipath.connector.uipath-uipath-testmanager.insert-record`` etc.). BPMN
carries no per-operation node type. A generic record is any Test Manager
catalog object that supports the IS operation (``uip is resources list
uipath-uipath-testmanager``): an ``Intsvc.ActivityExecution`` node matches on
any such ``objectName`` + ``method``, an HTTP node on any such object's IS
enrichment path (``registry get`` without ``--input-details``) + HTTP verb,
every placeholder filled.

    insert a record -> Create,   POST            (11 objects)
    get a record    -> Retrieve, GETBYID (HTTP GET) (10 objects)
    update a record -> Update,   PATCH or PUT     (4 objects)
    delete a record -> Delete,   DELETE           (5 objects)
    list records    -> List,     GET              (15 objects)

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_generic_records.py
    python3 $REFERENCE_DIR/_shared/check_testmanager_generic_records.py --all-ops

With no arguments: asserts at least one sendTask calls the Test Manager
connector, in either shape.
With ``--all-ops``: additionally asserts all five generic-record operations
are present, each as its own distinct sendTask.
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

CREATE = [
    ("AssignTestCasesToRequirement", "/v2/{ProjectId}/requirements/{Id}/assigntestcases"),
    ("AssignTestCasesToTestSet", "/v2/{ProjectId}/testsets/{id}/assigntestcases"),
    ("CreateDefect", "/v2/{ProjectId}/defects"),
    ("ExecuteTestCases", "/v2/{ProjectId}/testcases/startexecute"),
    ("ExecuteTestSet", "/v2/{ProjectId}/testsets/{testSetId}/startexecute"),
    ("ReportRunCheckpoint", "/v2/factories/runs/checkpoints"),
    ("Requirement", "/v2/{ProjectId}/requirements"),
    ("TestCase", "/v2/{ProjectId}/testcases"),
    ("TestSet", "/v2/{ProjectId}/testsets"),
    ("TestStep", "/v2/{ProjectId}/teststeps"),
    ("UploadAttachment", "/v2/{projectId}/attachments/{objType}/{id}/upload"),
]
RETRIEVE = [
    ("DownloadAssertion",
     "/v2/{projectId}/testcaselogartifacts/{id}/assertions/{assertionId}/downloadscreenshot"),
    ("DownloadAttachment", "/v2/{projectId}/attachments/{objectType}/{id}/download"),
    ("GetDefect", "/v2/{ProjectId}/defects/{id}"),
    ("GetProjectByPrefix", "/v2/projects/prefix/{projectPrefix}"),
    ("Requirement", "/v2/{ProjectId}/requirements/{id}"),
    ("TestCase", "/v2/{ProjectId}/testcases/{id}"),
    ("TestCaseLog", "/v2/{projectId}/testcaselogs/{id}"),
    ("TestExecution", "/v2/{projectId}/testexecutions/{id}"),
    ("TestSet", "/v2/{ProjectId}/testsets/{id}"),
    ("TestStep", "/v2/{ProjectId}/teststeps/{id}"),
]
UPDATE = [
    ("Requirement", "/v2/{ProjectId}/requirements/{id}"),
    ("TestCase", "/v2/{ProjectId}/testcases/{id}"),
    ("TestSet", "/v2/{ProjectId}/testsets/{id}"),
    ("TestStep", "/v2/{ProjectId}/teststeps/{id}"),
]
DELETE = [
    ("DeleteAttachment", "/v2/{projectId}/attachments/{objectType}/{id}"),
    ("Requirement", "/v2/{ProjectId}/requirements/{id}"),
    ("TestCase", "/v2/{ProjectId}/testcases/{id}"),
    ("TestExecution", "/v2/{projectId}/testexecutions/{id}"),
    ("TestSet", "/v2/{ProjectId}/testsets/{id}"),
]
LIST = [
    ("GetAssertions", "/v2/{projectId}/testcaselogartifacts/{id}/assertions"),
    ("GetAssignedTestCasesForRequirement", "/v2/{ProjectId}/requirements/{Id}/assignedtestcaseids"),
    ("GetAssignedTestCasesForTestSet", "/v2/{ProjectId}/testsets/{id}/assignedtestcaseids"),
    ("GetAttachments", "/v2/{projectId}/attachments/{ObjectType}/{Id}/all"),
    ("GetImpactedTransactions", "/v2/{ProjectId}/sapplanner/transports/coverage"),
    ("GetRobotLogs", "/v2/{projectId}/orchestrator/testexecution/{id}/robotlogs/paged"),
    ("GetTestCaseLogsOfTestExecution",
     "/v2/{projectId}/testcaselogs/testexecution/{testExecutionId}/paged"),
    ("GetTestStepLogs", "/v2/{projectId}/teststeplogs"),
    ("GetTestSteps", "/v2/{ProjectId}/teststeps/testcase/{Id}"),
    ("Project", "/v2/projects"),
    ("Requirement", "/v2/{ProjectId}/requirements"),
    ("TestCase", "/v2/{ProjectId}/testcases"),
    ("TestExecution", "/v2/{projectId}/testexecutions"),
    ("TestManagerEvents", "/TestManagerEvents"),
    ("TestSet", "/v2/{ProjectId}/testsets"),
]


def _any_object(label: str, methods: set[str], targets: list[tuple[str, str]]) -> ConnectorOperation:
    (object_name, path), *alternatives = targets
    return ConnectorOperation(label, object_name, methods, path, tuple(alternatives))


OPERATIONS = [
    _any_object("insert a record", {"post"}, CREATE),
    _any_object("get a record", {"getbyid"}, RETRIEVE),
    _any_object("update a record", {"patch", "put"}, UPDATE),
    _any_object("delete a record", {"delete"}, DELETE),
    _any_object("list records", {"get"}, LIST),
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

    require_operations(requests, OPERATIONS, "generic record")
    print("OK: all five generic record operations present as distinct connector nodes")


if __name__ == "__main__":
    main()
