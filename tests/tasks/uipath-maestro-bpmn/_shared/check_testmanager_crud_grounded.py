#!/usr/bin/env python3
"""Data-grounded Test Manager Create+Get round-trip (BPMN).

Ported from Flow `connector_features/testmanager_crud_grounded/check.py` and
its sibling criterion's
``_shared/flow_contains.py 'uipath-uipath-testmanager.create-test-case' 'uipath-uipath-testmanager.get-test-case'``.

Flow's ``check.py`` proves a REAL create->read round-trip through the
connector by comparing two files the run itself produced -- the pre_run
seed (``seed.json``) and the agent's own report of what it sent/received
(``result.json``) -- without parsing the ``.flow`` artifact at all. That
comparison is file-format-agnostic, so it ports unchanged: ``round_trip()``
and ``execution_evidence()`` below are Flow's ``main()`` verbatim, modulo the
process/flow vocabulary in messages.

The one Flow assertion that DOES read the artifact -- the sibling
``flow_contains`` criterion's two node-type substrings -- is retargeted here
from Flow's per-operation JSON node ``type`` string to the sendTasks that
call the Test Manager connector (``bpmn_check.connector_requests``),
classified exactly as ``_shared/check_testmanager_testcase_lifecycle.py``
does, restricted to the two operations this task's Flow prompt asks for:
``Intsvc.ActivityExecution`` by objectName + method (TestCase/POST = create,
TestCase/GETBYID|GET = get), connector-mode ``Intsvc.UnifiedHttpRequest`` by
method + IS enrichment path, every placeholder filled (POST
``/v2/{ProjectId}/testcases`` = create, GET ``/v2/{ProjectId}/testcases/{id}``
= get). A manual-mode request, or one through another connector, does not
count.

Assertion map (Flow -> BPMN):
  F check.py:29-32  created_name == seed["name"]                       -> round_trip() (default)
  F check.py:31-32  retrieved_name == seed["name"]                     -> round_trip() (default)
  F check.py:33-34  id present                                         -> round_trip() (default)
  F check.py:24-26  created_name/retrieved_name/id all present         -> execution_evidence() (--execution-evidence)
  F criterion 2     flow_contains 'uipath-uipath-testmanager.create-test-case'
                     'uipath-uipath-testmanager.get-test-case'          -> node_types() (--node-types)
  I                 locate/read seed.json, result.json                  -> load_json()
  I                 locate/parse .bpmn (node-types mode only)            -> parse_bpmn()
  T                 objectName+method or method+path classification
                     (see check_testmanager_testcase_lifecycle.py)       -> OPERATIONS / require_operations()
  T                 GETBYID/GET equivalence for "get the test case"     -> OPERATIONS methods set

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_testmanager_crud_grounded.py --node-types
    python3 $REFERENCE_DIR/_shared/check_testmanager_crud_grounded.py --execution-evidence
    python3 $REFERENCE_DIR/_shared/check_testmanager_crud_grounded.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    ConnectorOperation,
    connector_requests,
    parse_bpmn,
    require_operations,
)

CONNECTOR_KEY = "uipath-uipath-testmanager"
OPERATIONS = [
    ConnectorOperation("create a test case", "TestCase", {"post"},
                       "/v2/{ProjectId}/testcases"),
    ConnectorOperation("get the test case", "TestCase", {"getbyid", "get"},
                       "/v2/{ProjectId}/testcases/{id}"),
]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def load_json(path: str, what: str) -> dict:
    try:
        return json.load(open(path, encoding="utf-8"))
    except OSError:
        fail(f"{path} missing ({what})")
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    return {}  # unreachable: fail() exits, but satisfies static analysis


def node_types() -> None:
    """F criterion 2: BPMN carries a create AND a get Test Manager connector node."""
    path, root = parse_bpmn()
    requests = list(connector_requests(root, CONNECTOR_KEY))
    if not requests:
        fail(
            "no bpmn:sendTask calls the Test Manager connector: expected "
            f"Intsvc.ActivityExecution with connectorKey {CONNECTOR_KEY!r}, or a "
            "connector-mode Intsvc.UnifiedHttpRequest with targetConnector "
            f"{CONNECTOR_KEY!r}"
        )

    require_operations(requests, OPERATIONS, "Test Manager create/get")
    print(f"OK: create and get Test Manager connector nodes present in {path}")


def execution_evidence() -> None:
    """F check.py:24-26: result.json records all three fields (weak presence check)."""
    load_json("seed.json", "pre_run did not run")
    res = load_json("result.json", "agent did not record the create/get round-trip")
    if not all(res.get(key) for key in ("created_name", "retrieved_name", "id")):
        fail("result.json is missing created_name, retrieved_name, or id")
    print("OK: execution result recorded")


def round_trip() -> None:
    """F check.py:29-34: retrieved value equals the unique seeded value (strict)."""
    seed = load_json("seed.json", "pre_run did not run")
    res = load_json("result.json", "agent did not record the create/get round-trip")
    name = seed["name"]
    if res.get("created_name") != name:
        fail(f"created_name {res.get('created_name')!r} != seeded {name!r}")
    if res.get("retrieved_name") != name:
        fail(f"retrieved_name {res.get('retrieved_name')!r} != seeded {name!r} — value did not round-trip")
    if not res.get("id"):
        fail("no id captured from the create response")
    print(f"OK: real round-trip verified — created & retrieved {name!r} (id {res['id']})")


def main() -> None:
    args = sys.argv[1:]
    if "--node-types" in args:
        node_types()
    elif "--execution-evidence" in args:
        execution_evidence()
    else:
        round_trip()


if __name__ == "__main__":
    main()
