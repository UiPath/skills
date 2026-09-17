#!/usr/bin/env python3
"""Shape criterion (weight 3.0): the submitted solution wires the delegated
resource into the BPMN through the REAL runtime contract, not the
resolvable-looking-but-broken registry template.

Per row in composition.RESOURCES:
  1. The resource's project is present inside the submitted solution AND
     registered in its `.uipx`.
  2. The wrapper serviceTask carries exactly the row's required context
     fields, correctly shaped -- for the API-workflow row (SKILL.md rule 18 /
     references/registry-workflow.md): `releaseKey` bound via
     `=bindings.<id>` to a `resource="process" propertyAttribute="Key"`
     binding whose `default` matches the resource's REAL process Key, and a
     LITERAL `folderKey` matching the seeded folder's REAL FolderKey GUID.
     None of the broken template's `folderId`/`folderPath`/`name` fields
     survive.
  3. `JobArguments` passes the caller's value by reference (`=vars.<id>` or
     `=js:`), never a literal.
  4. Every `vars.<id>` read anywhere in the process is declared.
  5. The invoking node's own output variable is the one an end event maps
     out, and that end-event mapping publishes the row's declared output --
     so the exposed value cannot come from an unrelated node.
  6. `entry-points.json` publishes the process's declared input(s) and every
     row's declared output.
  7. LIVE: `uip maestro bpmn validate` reports `Status: "Valid"` with no
     `VARIABLE_DOES_NOT_EXIST` warning. `VARIABLE_NOT_SET` on the node
     reading the start-event-scoped input is expected BY CONSTRUCTION (the
     BPMN skill's own guidance) and is never gated on here.

Steps 1-6 are pure and unit-tested offline against fixtures/gold and
fixtures/mutations/ in test_checks.py, with the live resolvers (steps 2's
cross-tenant match) injected as plain callables so no tenant call is needed
to prove the checking LOGIC is correct. main() below wires the real `uip`
calls for an actual run.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import composition  # noqa: E402

_shared_dir = HERE
while _shared_dir != os.path.dirname(_shared_dir) and not os.path.isdir(
    os.path.join(_shared_dir, "_shared")
):
    _shared_dir = os.path.dirname(_shared_dir)
sys.path.insert(0, _shared_dir)

from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    get_ci,
    parse_json_output,
    payload_data,
    run_cli,
)

VALIDATE_TIMEOUT = 120
FOLDERS_GET_TIMEOUT = 60
PROCESSES_LIST_TIMEOUT = 60


# ---------------------------------------------------------------------------
# Per-row structural + cross-tenant shape check (pure; live calls come from
# the resolvers the caller supplies)
# ---------------------------------------------------------------------------

def check_resource_row(
    *,
    root: Path,
    uipx_path: Optional[Path],
    process,
    row: dict[str, Any],
    resolve_release_key: composition.ReleaseKeyResolver = composition.never_resolves,
    resolve_folder_key: composition.FolderKeyResolver = composition.never_resolves,
) -> list[str]:
    problems: list[str] = []

    project_dir = composition.find_resource_project(root, row)
    if project_dir is None:
        problems.append(
            f"{row['kind']}: no project found under {root} matching markers "
            f"{row['markers']}"
        )
    elif uipx_path is None:
        problems.append(f"{row['kind']}: solution has no .uipx manifest")
    elif not composition.project_is_registered(uipx_path, project_dir):
        problems.append(
            f"{row['kind']}: project at {project_dir} is not registered in "
            f"{uipx_path.name}"
        )

    if process is None:
        problems.append(f"{row['kind']}: BPMN process element not found")
        return problems

    task = composition.find_wrapper_task(process, row["wrapper"])
    if task is None:
        problems.append(
            f"{row['kind']}: no serviceTask with uipath:type {row['wrapper']!r}"
        )
        return problems
    node_id = task.attrib.get("id")

    declared = composition.declared_variables(process)
    bindings = composition.bindings_index(process)
    context = composition.context_fields_of(task)

    for field_name, spec in row["context_fields"].items():
        if field_name not in context:
            problems.append(
                f"{row['kind']}: context field {field_name!r} missing on {node_id!r}"
            )
            continue
        value = context[field_name].get("value", "") or ""
        if spec["mode"] == "binding":
            match = re.fullmatch(r"=bindings\.([A-Za-z0-9_]+)", value)
            if not match:
                problems.append(
                    f"{row['kind']}: {field_name} must be bound via "
                    f"=bindings.<id>, got {value!r}"
                )
                continue
            binding_id = match.group(1)
            binding = bindings.get(binding_id)
            if binding is None:
                problems.append(
                    f"{row['kind']}: {field_name} references undeclared "
                    f"binding {binding_id!r}"
                )
                continue
            if (
                binding.get("resource") != spec["binding_resource"]
                or binding.get("propertyAttribute") != spec["binding_attr"]
            ):
                problems.append(
                    f"{row['kind']}: binding {binding_id} must be "
                    f"resource={spec['binding_resource']!r} "
                    f"propertyAttribute={spec['binding_attr']!r}, got "
                    f"resource={binding.get('resource')!r} "
                    f"propertyAttribute={binding.get('propertyAttribute')!r}"
                )
            default = binding.get("default", "") or ""
            resolved = resolve_release_key(binding)
            if resolved is not None and default.casefold() != resolved.casefold():
                problems.append(
                    f"{row['kind']}: binding {binding_id} default {default!r} "
                    f"does not match the resource's real process Key "
                    f"{resolved!r}"
                )
        elif spec["mode"] == "literal_guid":
            if value.startswith("="):
                problems.append(
                    f"{row['kind']}: {field_name} must be a literal GUID, "
                    f"not an expression: {value!r}"
                )
            elif not composition.GUID_RE.match(value):
                problems.append(f"{row['kind']}: {field_name} is not a GUID: {value!r}")
            else:
                resolved = resolve_folder_key()
                if resolved is not None and value.casefold() != resolved.casefold():
                    problems.append(
                        f"{row['kind']}: {field_name} {value!r} does not match "
                        f"the seeded folder's real FolderKey {resolved!r}"
                    )
        else:  # pragma: no cover - table author error, not a submission defect
            raise composition.CompositionError(f"unknown context-field mode {spec['mode']!r}")

    forbidden = [name for name in row.get("forbidden_context_fields", ()) if name in context]
    if forbidden:
        problems.append(
            f"{row['kind']}: context still carries the broken template's "
            f"field(s) {forbidden} on {node_id!r} (rule 18 -- releaseKey + "
            "folderKey only, never name/folderPath/folderId)"
        )

    job_args = composition.job_arguments_text(task)
    if not job_args:
        problems.append(f"{row['kind']}: {node_id!r} has no JobArguments input")
    else:
        refs = composition.var_refs_in(job_args)
        if not refs and "=js:" not in job_args:
            problems.append(
                f"{row['kind']}: JobArguments must reference a process "
                f"variable (=vars.<id> or =js:), got {job_args!r}"
            )

    node_output_var_ids = {
        vid
        for vid, meta in declared.items()
        if meta.get("name") == row["output"] and meta.get("elementId") == node_id
    }
    if not node_output_var_ids:
        problems.append(
            f"{row['kind']}: no variable named {row['output']!r} is declared "
            f"scoped to {node_id!r} (elementId must match the invoking node)"
        )
    else:
        end_mappings = composition.end_event_mappings(process)
        end_sources = {m.get("source", "") for m in end_mappings}
        matched_targets = {
            m.get("var")
            for m in end_mappings
            if m.get("source", "").removeprefix("=vars.") in node_output_var_ids
        }
        if not any(f"=vars.{vid}" in end_sources for vid in node_output_var_ids):
            problems.append(
                f"{row['kind']}: node {node_id!r}'s own output variable(s) "
                f"{sorted(node_output_var_ids)} are never mapped out by an "
                "end event"
            )
        else:
            published_names = {
                declared[vid]["name"]
                for vid in matched_targets
                if vid in declared and declared[vid].get("kind") == "output"
            }
            if row["output"] not in published_names:
                problems.append(
                    f"{row['kind']}: the end-event mapping fed by {node_id!r} "
                    f"does not publish {row['output']!r} as a declared "
                    "process output"
                )

    return problems


def check_no_undeclared_var_reads(process) -> list[str]:
    declared = composition.declared_variables(process)
    referenced = composition.all_var_refs_in_process(process)
    undeclared = sorted(v for v in referenced if v not in declared)
    if undeclared:
        return [f"reads undeclared variable id(s) {undeclared}"]
    return []


def check_published_contract(
    process, entry_points: Optional[dict], resources: list[dict[str, Any]] = composition.RESOURCES
) -> list[str]:
    problems: list[str] = []
    if entry_points is None:
        return ["entry-points.json not found or unreadable"]

    declared = composition.declared_variables(process)
    start_input_names = sorted({
        meta["name"] for meta in declared.values() if meta.get("kind") == "input" and meta.get("name")
    })
    in_props = composition.entry_point_input_properties(entry_points)
    missing_inputs = [n for n in start_input_names if n not in in_props]
    if missing_inputs:
        problems.append(f"entry-points.json input does not publish {missing_inputs}")

    out_props = composition.entry_point_output_properties(entry_points)
    for row in resources:
        if row["output"] not in out_props:
            problems.append(
                f"entry-points.json output does not publish {row['output']!r} "
                f"(required by the {row['kind']} row)"
            )

    if not start_input_names:
        problems.append("no process input is declared at all")
    if not out_props and not any(row["output"] for row in resources):
        problems.append("entry-points.json declares no output at all")

    return problems


def collect_shape_problems(
    root: Path,
    *,
    resolve_release_key_for_row=lambda row, project_dir: composition.never_resolves,
    resolve_folder_key: composition.FolderKeyResolver = composition.never_resolves,
    resources: list[dict[str, Any]] = composition.RESOURCES,
) -> list[str]:
    """Every structural + cross-tenant shape rule except the live `validate`
    gate (which needs a real CLI call and is checked separately). Pure given
    its resolvers, so this is the one entry point both main() and
    test_checks.py call -- the tests just inject resolvers that return
    fixture-matching constants instead of shelling out to `uip`.

    `resolve_release_key_for_row(row, project_dir)` lets each row build its
    own resolver from its own discovered project (v1 has one row; Phase 5's
    second row needs its own project hint too).
    """

    uipx_path = composition.find_uipx(root)
    bpmn_path = composition.find_bpmn(root)
    if bpmn_path is None:
        return ["no .bpmn file found under the solution root"]
    process = composition.parse_process(bpmn_path)
    entry_points = composition.load_entry_points(bpmn_path.parent)

    problems: list[str] = []
    for row in resources:
        project_dir = composition.find_resource_project(root, row)
        problems += check_resource_row(
            root=root,
            uipx_path=uipx_path,
            process=process,
            row=row,
            resolve_release_key=resolve_release_key_for_row(row, project_dir),
            resolve_folder_key=resolve_folder_key,
        )
    problems += check_no_undeclared_var_reads(process)
    problems += check_published_contract(process, entry_points, resources)
    return problems


# ---------------------------------------------------------------------------
# Live `uip maestro bpmn validate` gate (rule: chase VARIABLE_DOES_NOT_EXIST
# only -- VARIABLE_NOT_SET on the start-event-scoped input is by construction)
# ---------------------------------------------------------------------------

def assert_validate_clean(validate_payload: dict) -> list[str]:
    data = get_ci(validate_payload, "Data", {}) or {}
    problems: list[str] = []
    status = get_ci(data, "Status")
    if status != "Valid":
        problems.append(f"validate Status is {status!r}, expected 'Valid'")
    warnings = get_ci(data, "Warnings", []) or []
    bad = [
        w
        for w in warnings
        if isinstance(w, dict) and (w.get("Code") or w.get("code")) == "VARIABLE_DOES_NOT_EXIST"
    ]
    if bad:
        problems.append(f"validate reported VARIABLE_DOES_NOT_EXIST: {bad}")
    return problems


# ---------------------------------------------------------------------------
# Live resolvers
# ---------------------------------------------------------------------------

def live_folder_key_resolver(folder_path: str) -> composition.FolderKeyResolver:
    def resolve() -> Optional[str]:
        completed = run_cli(["uip", "or", "folders", "get", folder_path], timeout=FOLDERS_GET_TIMEOUT)
        try:
            _payload, data = payload_data(completed, "folders get", require_success=True)
        except CheckFailure as error:
            print(f"WARN: could not resolve the seeded folder's real Key: {error}")
            return None
        key = get_ci(data, "Key")
        return key if isinstance(key, str) else None

    return resolve


def live_release_key_resolver(folder_path: str, project_name_hint: str) -> composition.ReleaseKeyResolver:
    def resolve(_binding: dict[str, str]) -> Optional[str]:
        completed = run_cli(
            [
                "uip", "or", "processes", "list",
                "--folder-path", folder_path,
                "--all-fields",
                "--limit", "200",
            ],
            timeout=PROCESSES_LIST_TIMEOUT,
        )
        try:
            _payload, data = payload_data(completed, "processes list", require_success=True)
        except CheckFailure as error:
            print(f"WARN: could not resolve the resource's real process Key: {error}")
            return None
        rows = data if isinstance(data, list) else []
        needle = project_name_hint.casefold()
        matches = [
            row
            for row in rows
            if needle in str(get_ci(row, "Name", "") or "").casefold()
            or needle in str(get_ci(row, "ProcessKey", "") or get_ci(row, "ProcessName", "") or "").casefold()
        ]
        if len(matches) != 1:
            print(
                f"WARN: expected exactly one deployed process matching "
                f"{project_name_hint!r} in {folder_path!r}, found {len(matches)}; "
                "skipping the cross-tenant Key match"
            )
            return None
        key = get_ci(matches[0], "Key")
        return key if isinstance(key, str) else None

    return resolve


def main() -> None:
    seed_path = Path("seed.json")
    if not seed_path.is_file():
        raise SystemExit("FAIL: seed.json is missing; pre_run did not complete")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    folder_path = f"{seed['parentFolderPath']}/{seed['folderName']}"

    root = Path(".")
    bpmn_path = composition.find_bpmn(root)
    if bpmn_path is None:
        raise SystemExit("FAIL: no .bpmn file found in the submitted solution")
    project_dir = bpmn_path.parent

    problems: list[str] = collect_shape_problems(
        root,
        resolve_release_key_for_row=lambda row, project: live_release_key_resolver(
            folder_path, project.name if project is not None else row["kind"]
        ),
        resolve_folder_key=live_folder_key_resolver(folder_path),
    )

    validate = run_cli(["uip", "maestro", "bpmn", "validate", str(project_dir)], timeout=VALIDATE_TIMEOUT)
    validate_payload = parse_json_output(validate.stdout or validate.stderr, "validate")
    problems += assert_validate_clean(validate_payload)

    if problems:
        print("FAIL: shape check found the following problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)

    print(f"PASS: shape check clean for {len(composition.RESOURCES)} resource row(s)")


if __name__ == "__main__":
    main()
