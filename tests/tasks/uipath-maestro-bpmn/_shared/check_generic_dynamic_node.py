#!/usr/bin/env python3
"""AcrUserList generic dynamic node (BPMN): structural + live checks.

Ported from Flow `connector_features/generic_dynamic_node/_shared/check_generic_dynamic_node.py`:
same scenario (a manual-start process calls ServiceNow's generic, object-agnostic
"List Records" activity — display name "List All Records" — on the dynamically
resolved `acr_user` object, then surfaces the result as a process output),
translated from a JSON node walk + inline `flow debug` payload to an XML walk
over the registry-driven `Intsvc.ActivityExecution` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §3) plus the BPMN
live-debug surface (`_shared/bpmn_live.py`, per LIVE-ADDENDUM's canonical
pattern: ephemeral solution import, `bpmn debug`, `debug-instance
variables-all`/`incidents`, cloned from `check_jira_get_issue.py`).

A generic activity encodes only the operation (List) in its registry type; the
object (`acr_user`) is supplied dynamically at authoring time via
`uip maestro bpmn registry get Intsvc.ActivityExecution --connection-id <id>
--object-name acr_user` — the BPMN analog of Flow's "set the object name on
the node". Confirmed live against this tenant's ServiceNow catalog
(`uip is activities list uipath-servicenow-servicenow --output json`):
`ListAllRecords` / "List Records" is `IsCurated: No`, `ObjectName: N/A`,
`Operation: List` — i.e. the generic (non-curated) form is the ONLY form for
this activity, unlike the curated-or-generic ambiguity BATCH1-ADDENDUM
describes for Data Service/Test Manager. The enrichment call above (run
read-only against the live tenant while authoring this port) confirmed the
resulting context fields: `objectName=acr_user`, `operation=List`,
`method=GET`, `path=/acr_user`.

The `acr_user` table is empty in the codereval ServiceNow tenant, so the list
call legitimately returns `[]`. The runtime assertion therefore checks that
the connector completed with no incidents and surfaced an array-typed output
(empty allowed) — not that rows came back.

Exits non-zero on the first failure (``FAIL: ...``); prints ``OK: ...`` per
check.

Assertion map (Flow → BPMN):
  F check_generic_dynamic_node.py:128-146  assert_flow_uses_connector_target(CONNECTOR_KEY)
                                            → CONNECTOR_KEY substring present in raw .bpmn text (fast pre-check)
                                              + a node's connector_context()["connectorKey"] == CONNECTOR_KEY
  F check_generic_dynamic_node.py:108-125  _is_generic_list(): Generic activityType + `list` operation
                                            → is_generic_list_node(): a node carrying Intsvc.ActivityExecution
                                              whose connectorKey is uipath-servicenow-servicenow and whose
                                              objectName == "acr_user" with operation == "list" or method == "GET"
                                              (registry-confirmed above: the ONLY form ListAllRecords takes)
  F check_generic_dynamic_node.py:148-164  objectName resolved to OBJECT_NAME ("acr_user")
                                            → objectName context field == "acr_user" (folded into is_generic_list_node)
  F check_generic_dynamic_node.py:203-205  run_debug(...) implicitly requires finalStatus == "Completed"
                                            (flow_check.run_debug raises on a non-Completed status internally;
                                            `bpmn debug` returns only an instance id, so the check is explicit here)
                                            → FinalStatus in COMPLETED_STATUSES and debug-instance incidents is empty
  F check_generic_dynamic_node.py:167-200  _assert_array_output(): an array-typed global output (empty allowed),
                                            reporting a flattened sys_id-bearing record if present
                                            → array-typed value among the root scope's Globals AND every element's
                                              Outputs (LIVE-ADDENDUM: a root PUBLIC OUTPUT has read back null even
                                              when correctly mapped, so the search is not scoped to one declared
                                              output variable — mirrors check_jira_get_issue.collect_output_haystack)
  I                 locate/parse .bpmn, resolve project directory
                                            → bpmn_check.find_bpmn_file()/resolve_project()
  I                 ephemeral solution init + `solution projects import` + sha256 pin of the imported bytes
                    against the submitted file — `bpmn debug` runs against an imported project, unlike
                    `flow debug`, which runs directly against the discovered project directory
                                            → LIVE-ADDENDUM canonical live pattern (mirrors check_jira_get_issue.py)
  T                 Generic (non-curated) object CRUD classification (BATCH1-ADDENDUM): objectName == entity,
                    method GET (or operation "list") in place of a curated node-type slug
                                            → is_generic_list_node()
  DROPPED           OPERATION_SLUGS node-type-slug matching (Flow's `…list-records` / `…list-all-records`
                    substring fallback) — BPMN's registry type is always the fixed literal
                    `Intsvc.ActivityExecution`; there is no per-operation node-type slug to match against, so
                    the slug-matching branch of Flow's check drops entirely rather than translating. The
                    dynamically-resolved `objectName` context field (Flow's own preferred, slug-agnostic signal)
                    carries the whole check here.

No tenant re-read beyond the process's own debug run is performed, matching Flow's own grader (a read-only
list call has nothing else to verify against).
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# …/uipath-maestro-bpmn (for _shared), same convention as _shared/check_jira_get_issue.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: E402

from _shared.bpmn_check import find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    connector_context,
    get_ci,
    incident_records,
    payload_data,
    root_scope,
    run_cli,
    sha256,
)

CONNECTOR_KEY = "uipath-servicenow-servicenow"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"
# API object name (not the "Acr User" display name) — the registry's
# `--object-name` enrichment takes the connector's case-sensitive `Name`,
# which for this table is `acr_user`.
OBJECT_NAME = "acr_user"
GENERIC_LIST_OPERATIONS = {"list"}
GENERIC_LIST_METHODS = {"GET"}
NAME_HINT = "AcrUserList"

LIVE_RUN_DIR = Path("acr-user-list-live")
SOLUTION_INIT_TIMEOUT = 90
SOLUTION_IMPORT_TIMEOUT = 180
VARIABLES_ALL_TIMEOUT = 120
INCIDENTS_TIMEOUT = 120
COMPLETED_STATUSES = {"Completed", "Successful"}

# Worst-case wall clock this checker can spend, priced the way
# _shared/test_criterion_budgets.py prices a run_debug(...) call: the debug
# call below passes no timeout/retries/backoff kwargs, so it prices at
# bpmn_live.debug_budget() == bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT (480).
# The surrounding CLI steps (solution init/import, variables-all, incidents)
# are not priced by that guard, so their sum is added by hand here, exactly
# as check_jira_get_issue.py documents:
#   90 (solution init) + 180 (solution import) + 480 (debug)
#   + 120 (variables-all) + 120 (incidents) = 990
#   + bpmn_live.CRITERION_MARGIN_SECONDS (60) = 1050
# Flow's own criterion timeout (720) does not cover this arithmetic — a
# single flow_check.run_debug(timeout=300) call has no separate solution
# init/import/variables-all/incidents steps — so the BPMN criterion timeout
# in generic_dynamic_node.yaml is raised to 1050 and documented there as the
# one sanctioned deviation from "criteria identical" (LIVE-ADDENDUM: the
# budget is a property of the CLI surface, not of what is graded).


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def is_generic_list_node(context: dict) -> bool:
    """Generic (non-curated) list activity: objectName == acr_user, list op.

    Registry-confirmed (see module docstring): ListAllRecords has no curated
    alternative for this connector, so objectName + operation/method is the
    whole signal — there is no node-type slug in BPMN to fall back on."""
    object_name = (context.get("objectName") or "").strip().lower()
    if object_name != OBJECT_NAME:
        return False
    operation = (context.get("operation") or "").strip().lower()
    method = (context.get("method") or "").strip().upper()
    return operation in GENERIC_LIST_OPERATIONS or method in GENERIC_LIST_METHODS


def find_generic_list_nodes(root: ET.Element) -> list[ET.Element]:
    """Every element carrying an Intsvc.ActivityExecution generic list op.

    Scans every descendant, not a fixed tag list (registry templates may emit
    a connector activity as sendTask, serviceTask, or a plain task) — mirrors
    bpmn_live.index_runtime_connectors' own scanning discipline.
    """
    found = []
    for node in root.iter():
        context = connector_context(node)
        if context.get("connectorKey") != CONNECTOR_KEY:
            continue
        if ACTIVITY_TYPE not in ET.tostring(node, encoding="unicode"):
            continue
        if is_generic_list_node(context):
            found.append(node)
    return found


def _array_leaves(value):
    """Yield every list found in ``value``, recursing through dict values."""
    if isinstance(value, list):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _array_leaves(v)


def collect_array_candidates(variables_data: object) -> list[tuple[str, list]]:
    """Array-typed values among the root scope's Globals AND every element's
    Outputs.

    A root public output has been observed to read back null even when
    correctly mapped (LIVE-ADDENDUM), so the search is not scoped to one
    declared output variable — mirrors check_jira_get_issue.py's
    collect_output_haystack, adapted to look for an array shape rather than a
    substring.
    """
    candidates: list[tuple[str, list]] = []
    globals_ = get_ci(root_scope(variables_data), "Globals", {}) or {}
    if isinstance(globals_, dict):
        for name, value in globals_.items():
            for array in _array_leaves(value):
                candidates.append((f"global {name!r}", array))
    for scope in get_ci(variables_data, "Variables", []) or []:
        for element in get_ci(scope, "Elements", []) or []:
            outputs = get_ci(element, "Outputs", {})
            for array in _array_leaves(outputs):
                candidates.append(
                    (f"element {get_ci(element, 'ElementId')!r} Outputs", array)
                )
    return candidates


def main() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    if CONNECTOR_KEY not in raw:
        _fail(f"{bpmn_path} does not reference the {CONNECTOR_KEY} connector")
    if OBJECT_NAME not in raw:
        _fail(f"{bpmn_path} does not reference the object {OBJECT_NAME!r}")
    print(f"OK: bpmn references {CONNECTOR_KEY} and object {OBJECT_NAME!r}")

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        _fail(f"{bpmn_path} is not well-formed XML: {exc}")

    list_nodes = find_generic_list_nodes(root)
    if not list_nodes:
        seen = sorted(
            {
                json.dumps(connector_context(node), sort_keys=True)
                for node in root.iter()
                if connector_context(node).get("connectorKey") == CONNECTOR_KEY
            }
        )
        _fail(
            f"No generic ServiceNow list activity found on the {CONNECTOR_KEY} "
            f"connector with objectName={OBJECT_NAME!r} (expected operation "
            f"'list' or method 'GET'). Connector node contexts seen: {seen}"
        )
    print(f"OK: found {len(list_nodes)} generic list node(s) on objectName={OBJECT_NAME!r}")

    project_dir = resolve_project(os.path.basename(bpmn_path))
    original_hash = sha256(Path(bpmn_path))

    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    solution_dir = LIVE_RUN_DIR / "AcrUserListLiveEval"
    initialized = run_cli(
        ["uip", "solution", "init", str(solution_dir)], timeout=SOLUTION_INIT_TIMEOUT
    )
    payload_data(initialized, "initialize ephemeral solution")
    solution_files = sorted(solution_dir.glob("*.uipx"))
    if len(solution_files) != 1:
        raise CheckFailure(
            f"solution init produced {len(solution_files)} .uipx files in "
            f"{solution_dir}, expected exactly one"
        )
    solution_file = solution_files[0]
    imported = run_cli(
        [
            "uip",
            "solution",
            "projects",
            "import",
            str(project_dir.resolve()),
            "--solutionFile",
            str(solution_file),
        ],
        timeout=SOLUTION_IMPORT_TIMEOUT,
    )
    payload_data(imported, "import exact BPMN project")
    imported_project = solution_dir / project_dir.name
    if sha256(imported_project / os.path.basename(bpmn_path)) != original_hash:
        raise CheckFailure("solution import changed the submitted BPMN bytes")
    print(f"OK: imported exact artifact (sha256={original_hash})")

    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    final_status = get_ci(debug_data, "FinalStatus")
    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, "variables-all")

    incidents = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
        timeout=INCIDENTS_TIMEOUT,
    )
    _payload, incidents_data = payload_data(incidents, "incidents")
    incidents_list = incident_records(incidents_data)

    if final_status not in COMPLETED_STATUSES:
        detail = []
        faulted = [
            f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
            for item in get_ci(debug_data, "ElementExecutions", []) or []
            if isinstance(item, dict)
            and str(get_ci(item, "Status") or "").casefold() != "completed"
        ]
        if faulted:
            detail.append(f"non-completed elements: {faulted}")
        if incidents_list:
            detail.append(f"incidents: {json.dumps(incidents_list)[:1500]}")
        raise CheckFailure(
            f"final status was {final_status!r}"
            + ("; " + "; ".join(detail) if detail else "")
        )
    if incidents_list is None:
        raise CheckFailure(f"incidents response has an unknown shape: {incidents_data!r}")
    if incidents_list:
        raise CheckFailure(f"unexpected incidents: {incidents_list}")
    print("OK: bpmn debug completed (FinalStatus=%s, no incidents)" % final_status)

    candidates = collect_array_candidates(variables_data)
    if not candidates:
        _fail(
            "No output variable holds an array — the connector result was not "
            "surfaced as a process output. Checked root Globals and every "
            "element's Outputs."
        )
    label, value = candidates[0]
    if value and all(isinstance(r, dict) for r in value) and any("sys_id" in r for r in value):
        print(
            f"OK: connector returned {len(value)} Acr User record(s) in {label} "
            f"(first sys_id={value[0].get('sys_id')!r})"
        )
    else:
        print(
            f"OK: connector completed and surfaced an array output in {label} "
            f"({len(value)} record(s)). Empty is expected — the acr_user table "
            "is empty in this tenant."
        )
    print("PASS: all AcrUserList generic dynamic node checks passed")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
