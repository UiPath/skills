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
                                            → array held by a root Global that is a declared process output
                                              (input echoes excluded); only when every declared output reads back
                                              null (LIVE-ADDENDUM: a root PUBLIC OUTPUT has read back null even
                                              when correctly mapped), an array in the Outputs of the generic list
                                              node(s) instead
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

from _shared.bpmn_check import fail, find_bpmn_file, resolve_project  # noqa: E402
from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    CheckFailure,
    connector_context,
    debug_evidence,
    element_output_records,
    get_ci,
    import_exact,
    input_echo_ids,
    normalized_identifier,
    q,
    require_clean_run,
    resolve_runtime_key,
    root_scope,
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


def declared_outputs(process: ET.Element) -> list[tuple[str, ...]]:
    """(id, name) of each process-level `uipath:output`, minus input echoes."""
    variables = process.find(
        f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}"
    )
    if variables is None:
        return []

    echoes = {normalized_identifier(name) for name in input_echo_ids(process)}
    outputs = []
    for node in variables.findall(q(UIPATH_NS, "output")):
        keys = tuple(
            key
            for key in (node.attrib.get("id"), node.attrib.get("name"))
            if key and normalized_identifier(key) not in echoes
        )
        if keys:
            outputs.append(keys)
    return outputs


def global_value(globals_: dict, identifier: str) -> object:
    wanted = normalized_identifier(identifier)
    if not any(normalized_identifier(key) == wanted for key in globals_):
        return None
    return resolve_runtime_key(globals_, identifier, "declared output")


def collect_array_candidates(
    variables_data: object,
    outputs: list[tuple[str, ...]],
    list_node_ids: tuple[str, ...],
) -> list[tuple[str, list]]:
    """Arrays held by declared output globals; the list nodes' Outputs only
    when every declared output reads back null (LIVE-ADDENDUM)."""
    globals_ = get_ci(root_scope(variables_data), "Globals", {}) or {}
    if not isinstance(globals_, dict):
        globals_ = {}

    candidates: list[tuple[str, list]] = []
    read_back = False
    for keys in outputs:
        value = next(
            (v for v in (global_value(globals_, key) for key in keys) if v is not None),
            None,
        )
        if value is None:
            continue
        read_back = True
        if isinstance(value, list):
            candidates.append((f"output global {keys[0]!r}", value))
    if read_back:
        return candidates

    for outputs_record in element_output_records(variables_data, list_node_ids):
        for array in _array_leaves(outputs_record):
            candidates.append((f"list node Outputs {sorted(list_node_ids)}", array))
    return candidates


def main() -> None:
    bpmn_path = find_bpmn_file(NAME_HINT)
    raw = Path(bpmn_path).read_text(encoding="utf-8")
    if CONNECTOR_KEY not in raw:
        fail(f"{bpmn_path} does not reference the {CONNECTOR_KEY} connector")
    if OBJECT_NAME not in raw:
        fail(f"{bpmn_path} does not reference the object {OBJECT_NAME!r}")
    print(f"OK: bpmn references {CONNECTOR_KEY} and object {OBJECT_NAME!r}")

    try:
        root = ET.parse(bpmn_path).getroot()
    except ET.ParseError as exc:
        fail(f"{bpmn_path} is not well-formed XML: {exc}")

    list_nodes = find_generic_list_nodes(root)
    if not list_nodes:
        seen = sorted(
            {
                json.dumps(connector_context(node), sort_keys=True)
                for node in root.iter()
                if connector_context(node).get("connectorKey") == CONNECTOR_KEY
            }
        )
        fail(
            f"No generic ServiceNow list activity found on the {CONNECTOR_KEY} "
            f"connector with objectName={OBJECT_NAME!r} (expected operation "
            f"'list' or method 'GET'). Connector node contexts seen: {seen}"
        )
    print(f"OK: found {len(list_nodes)} generic list node(s) on objectName={OBJECT_NAME!r}")

    process = root.find(q(BPMN_NS, "process"))
    if process is None:
        fail(f"{bpmn_path} has no bpmn:process")
    outputs = declared_outputs(process)
    if not outputs:
        fail("process declares no uipath:output variable to surface the records")
    list_node_ids = tuple(node.attrib["id"] for node in list_nodes if node.attrib.get("id"))

    project_dir = resolve_project(os.path.basename(bpmn_path))
    LIVE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    imported_project = import_exact(
        Path(bpmn_path), project_dir, LIVE_RUN_DIR / "AcrUserListLiveEval"
    )
    debug_data, instance_id = bpmn_live.run_debug(
        imported_project, {}, LIVE_RUN_DIR / "debug.log"
    )
    print(f"OK: debug completed (instance {instance_id})")

    evidence = debug_evidence(instance_id)
    require_clean_run(debug_data, evidence)

    candidates = collect_array_candidates(evidence.variables, outputs, list_node_ids)
    if not candidates:
        fail(
            "No output variable holds an array — the connector result was not "
            "surfaced as a process output. Checked declared output globals "
            f"{outputs} and, on null readback, the list node Outputs "
            f"{list(list_node_ids)}."
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
