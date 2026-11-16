#!/usr/bin/env python3
"""Behaviour criterion (weight 5.0): the composed resource actually ran.

Mints a fresh `tok<uuid8>` NOW (the agent never sees it, so it cannot be
hard-coded), runs the submitted process live via `uip maestro bpmn debug`,
and requires `FinalStatus == Completed`. For every row in
composition.RESOURCES, the token must round-trip through THAT row's own
invoking node: it must appear in the process's declared output global AND
in the invoking node's OWN `Outputs` in `debug-instance variables-all` --
per-node provenance, so a ScriptTask or an unrelated node cannot cover for
the resource never having been reached at runtime. This is the anti-cheat core of the suite.

Deliberately does NOT require any transformation of the token -- an
echo-only API workflow mapped straight through is valid, not a cheat.
check_shape.py guarantees the published value comes from the node's own
response. The Outputs check
is a leaf walk (every string leaf reachable from the node's Outputs), not a
`json.dumps(...)` substring test over the whole blob, so a token that only
appears in a key name or an unrelated field cannot pass. The complementary
guard against a decoy node forging the published value -- no OTHER element
may write to the invoking node's own output variable -- lives in
check_shape.py (a structural, offline-checkable rule), not here.

`assert_row_provenance` is pure (BPMN Element + a variables-all payload in,
problems raised out) and is unit-tested in test_checks.py with synthetic
payloads, including the "one node cannot cover for another" case. main()
below wires the live `uip maestro bpmn debug` / `debug-instance` calls.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import composition  # noqa: E402

_shared_dir = HERE
while _shared_dir != os.path.dirname(_shared_dir) and not os.path.isdir(
    os.path.join(_shared_dir, "_shared")
):
    _shared_dir = os.path.dirname(_shared_dir)
sys.path.insert(0, _shared_dir)

from _shared import bpmn_live  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    element_output_records,
    get_ci,
    incident_records,
    payload_data,
    root_scope,
    run_cli,
    run_debug,
)

COMPLETED_STATUSES = {"Completed", "Successful"}
INCIDENTS_TIMEOUT = 120
VARIABLES_ALL_TIMEOUT = 120
DEBUG_TIMEOUT_SECONDS = bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT

# Priced the same way _shared/bpmn_live.py's own module docstring prices
# run_debug: the worst-case wall clock this criterion spends on live calls.
STEP_TIMEOUTS = (DEBUG_TIMEOUT_SECONDS, INCIDENTS_TIMEOUT, VARIABLES_ALL_TIMEOUT)


def _string_leaves(value: Any) -> list[str]:
    """Every string leaf reachable from `value` by descending dicts/lists.

    Used instead of a whole-blob `json.dumps(...)` substring test: the token
    must actually appear as (part of) some scalar the resource produced, not
    merely somewhere in the serialized JSON (a key name, a coincidental
    substring of an unrelated field, ...)."""

    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [leaf for item in value.values() for leaf in _string_leaves(item)]
    if isinstance(value, list):
        return [leaf for item in value for leaf in _string_leaves(item)]
    return []


def assert_row_provenance(
    row: dict[str, Any],
    process,
    variables_data: object,
    token: str,
) -> None:
    """Raise CheckFailure unless the token round-tripped through the row's
    OWN invoking node -- never through some other node's output.

    Deliberately does NOT require any transformation -- an echo API workflow
    mapped straight through, or one wrapped in `=js:'Hello, ' + ...`, is a
    valid, intended shape, not a cheat. What this DOES still guard: (a) the
    token must appear somewhere in the invoking node's own runtime Outputs
    (a leaf walk, not a substring-of-the-whole-blob test), and (b) no other
    element may have written the node-scoped output variable itself (see
    check_shape.py's "foreign write" scan) -- so a decoy cannot fake having
    produced the published value.
    """

    task = composition.find_wrapper_task(process, row["wrapper"])
    if task is None:
        raise CheckFailure(
            f"{row['kind']}: no serviceTask with uipath:type {row['wrapper']!r} "
            "to verify at runtime"
        )
    node_id = task.attrib.get("id")

    declared = composition.declared_variables(process)
    output_var_ids = {
        vid
        for vid, meta in declared.items()
        if meta.get("name") == row["output"] and meta.get("kind") == "output"
    }
    if not output_var_ids:
        raise CheckFailure(f"{row['kind']}: no declared process output named {row['output']!r}")

    globals_map = get_ci(root_scope(variables_data), "Globals", {})
    if not isinstance(globals_map, dict):
        raise CheckFailure("variables-all root scope Globals is not a map")

    _unset = object()
    published_value = _unset
    for vid in output_var_ids:
        try:
            published_value = bpmn_live.resolve_runtime_key(globals_map, vid, "runtime Globals")
        except CheckFailure:
            continue
        else:
            break
    if published_value is _unset:
        raise CheckFailure(
            f"{row['kind']}: declared output {row['output']!r} never appears "
            "in the runtime Globals"
        )
    if token not in str(published_value):
        raise CheckFailure(
            f"{row['kind']}: output {row['output']!r} ({published_value!r}) "
            f"does not contain the minted token {token!r}"
        )

    node_outputs = element_output_records(variables_data, (node_id,))
    if not node_outputs:
        raise CheckFailure(
            f"{row['kind']}: invoking node {node_id!r} produced no runtime "
            "Outputs -- was it ever executed?"
        )
    leaves = [leaf for output in node_outputs for leaf in _string_leaves(output)]
    if not any(token in leaf for leaf in leaves):
        raise CheckFailure(
            f"{row['kind']}: token {token!r} never appears in invoking node "
            f"{node_id!r}'s own Outputs -- another node may be covering for it"
        )


def assert_completed(debug_data: object, incidents_data: object) -> None:
    final_status = get_ci(debug_data, "FinalStatus")
    if final_status in COMPLETED_STATUSES:
        return
    detail = []
    faulted = [
        f"{get_ci(item, 'ElementId')}={get_ci(item, 'Status')}"
        for item in get_ci(debug_data, "ElementExecutions", []) or []
        if isinstance(item, dict)
        and str(get_ci(item, "Status") or "").casefold() != "completed"
    ]
    if faulted:
        detail.append(f"non-completed elements: {faulted}")
    records = incident_records(incidents_data)
    if records:
        detail.append(f"incidents: {json.dumps(records)[:1500]}")
    raise CheckFailure(
        f"final status was {final_status!r}" + ("; " + "; ".join(detail) if detail else "")
    )


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")

    root = Path(".")
    bpmn_path = composition.find_bpmn(root)
    if bpmn_path is None:
        raise SystemExit("FAIL: no .bpmn file found in the submitted solution")
    process = composition.parse_process(bpmn_path)
    project_dir = bpmn_path.parent

    declared = composition.declared_variables(process)
    start_input_names = sorted({
        meta["name"] for meta in declared.values() if meta.get("kind") == "input" and meta.get("name")
    })
    if len(start_input_names) != 1:
        raise SystemExit(
            f"FAIL: expected exactly one declared process input, found {start_input_names}"
        )
    input_name = start_input_names[0]

    token = f"tok{uuid.uuid4().hex[:8]}"
    # Literal, not DEBUG_TIMEOUT_SECONDS: test_criterion_budgets.py prices
    # run_debug calls statically off the AST and refuses a non-literal
    # timeout/budget argument. Keep this equal to DEBUG_TIMEOUT_SECONDS
    # (bpmn_live.DEBUG_BUDGET_DEFAULT_TIMEOUT) above.
    debug_data, instance_id = run_debug(
        project_dir, {input_name: token}, Path("debug.log"), timeout=480
    )
    print(f"OK: debug completed (instance {instance_id})")

    incidents_data = None
    if get_ci(debug_data, "FinalStatus") not in COMPLETED_STATUSES:
        incidents = run_cli(
            ["uip", "maestro", "bpmn", "debug-instance", "incidents", instance_id],
            timeout=INCIDENTS_TIMEOUT,
        )
        _payload, incidents_data = payload_data(incidents, "incidents", require_success=False)

    try:
        assert_completed(debug_data, incidents_data)
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error

    variables = run_cli(
        ["uip", "maestro", "bpmn", "debug-instance", "variables-all", instance_id],
        timeout=VARIABLES_ALL_TIMEOUT,
    )
    _payload, variables_data = payload_data(variables, "variables-all")

    try:
        for row in composition.RESOURCES:
            assert_row_provenance(row, process, variables_data, token)
            print(f"OK: {row['kind']} -- token round-tripped through its own {row['wrapper']} node")
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error

    print(
        "PASS: process ran to completion and every composed resource's own "
        "invoking node produced the round-tripped token"
    )


if __name__ == "__main__":
    main()
