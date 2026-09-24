#!/usr/bin/env python3
"""SupplierOnboarding: resource resolution against the live tenant.

The staged SDD pins real identities — 6 API workflows, 2 agents, 1 process, 1
child case, 9 dedicated Action Apps plus the shared
Guardrail.Escalation.Action.App, and the Outlook 365 connection / activity type.
This grader asserts the build bound them instead of emitting placeholders:

- no task left unresolved (`data: {}` / literal name+folder / bare connector)
- every non-connector binding pair is `resourceKey == "<folderPath>.<name>"`
  (implementation.md Step 12 Check 11 — a tenant GUID copied into resourceKey
  passes `validate` and only faults at `case debug`)
- every SDD deployment folder is bound, with the `resource` /
  `resourceSubType` its task type requires
- the connection ID and activity type ID reach caseplan.json, and the
  connection also reaches the bindings_v2.json sidecar (Check 7 parity)

API-workflow `name` defaults are deliberately not pinned: the resourceKey
suffix is the resolved registry entry's `name`, which is often the generic
"API Workflow" (plugins/tasks/api-workflow/planning.md).
"""

from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))

import supplier_onboarding_expected as E  # noqa: E402
from supplier_onboarding_plan import (  # noqa: E402
    binding_value,
    fail,
    find_stages,
    find_task,
    load_plan,
    stage_of,
    tasks_of,
)

BINDING_REF = "=bindings."
RESOURCE_KIND = {
    **{name: "api-workflow" for name in E.API_WORKFLOWS},
    **{name: "agent" for name in E.AGENTS},
    **{name: "process" for name in E.PROCESSES},
    **{name: "case-management" for name in E.CHILD_CASES},
    **{name: "action" for name in E.ACTION_APPS},
    E.SHARED_ESCALATION_APP: "action",
}
# Resources whose binding `name` default must be the SDD name verbatim.
PINNED_NAMES = [
    name for name in RESOURCE_KIND if name not in set(E.API_WORKFLOWS)
]


def task_label(task: dict) -> str:
    return (
        task.get("displayName")
        or (task.get("data") or {}).get("label")
        or task.get("id")
        or "<unnamed>"
    )


def binding_refs(task: dict) -> set[str]:
    """Every ``=bindings.<id>`` reference anywhere inside a task."""
    refs: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str) and value.startswith(BINDING_REF):
            refs.add(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(task)
    return refs


def connector_is_resolved(plan: dict, task: dict) -> list[str]:
    """Resolution problems for one connector task, tolerant of either shape.

    Phase 2 / graceful-degradation keeps ``typeId`` + ``connectionId`` on
    ``data``; the fully-populated Phase 3 shape carries the CLI-authoritative
    ``context[]`` instead, where the connection arrives as a ``=bindings.<id>``
    reference. Both count as resolved.
    """
    problems: list[str] = []
    data = task.get("data") or {}
    blob = json.dumps(task, default=str).lower()
    populated = bool(data.get("context")) or bool(
        data.get("typeId") and data.get("connectionId")
    )
    if not populated:
        problems.append(
            "connector task is a stub — neither a populated data.context nor "
            "data.typeId + data.connectionId"
        )
    if E.CONNECTOR_KEY not in blob:
        problems.append(f"connector task does not name {E.CONNECTOR_KEY}")
    resolved = {
        str(binding_value(plan, ref) or "").lower() for ref in binding_refs(task)
    }
    if E.CONNECTION_ID not in blob and E.CONNECTION_ID not in resolved:
        problems.append(
            f"connector task is not bound to the SDD's Outlook 365 connection "
            f"{E.CONNECTION_ID} (neither inline nor through a bindings reference)"
        )
    return problems


def check_resolved(plan: dict) -> None:
    unresolved: list[str] = []
    for stage in find_stages(plan, include_exception=True):
        for task in tasks_of(stage):
            data = task.get("data") or {}
            task_type = task.get("type")
            where = f"{task_label(task)} ({task_type})"
            if not data:
                unresolved.append(f"{where}: data is empty (placeholder task)")
                continue
            if task_type == E.CONNECTOR_TASK:
                unresolved.extend(
                    f"{where}: {problem}" for problem in connector_is_resolved(plan, task)
                )
                continue
            for field in ("name", "folderPath"):
                value = data.get(field)
                if not isinstance(value, str) or not value.startswith(BINDING_REF):
                    unresolved.append(
                        f"{where}: data.{field} must be an {BINDING_REF}<id> reference, "
                        f"got {value!r}"
                    )
            if task_type == "action" and not (data.get("taskTitle") or "").strip():
                unresolved.append(f"{where}: resolved action task needs a non-empty data.taskTitle")
    if unresolved:
        fail("unresolved / placeholder tasks:\n  - " + "\n  - ".join(unresolved))


def check_task_resource_pairing(plan: dict) -> None:
    """Each task binds the §4 resource its "Used By Tasks" row names."""
    problems: list[str] = []
    for stage_name, specs in E.TASKS.items():
        stage = stage_of(plan, stage_name)
        for spec in specs:
            if spec["type"] == E.CONNECTOR_TASK:
                continue
            task = find_task(plan, stage, spec["name"])
            if task is None:
                problems.append(f"{stage_name} / {spec['name']}: task not found")
                continue
            expected = E.RESOURCE_FOLDERS[E.TASK_RESOURCE[spec["name"]]]
            actual = binding_value(plan, (task.get("data") or {}).get("folderPath"))
            if E.norm(actual) != E.norm(expected):
                problems.append(
                    f"{stage_name} / {spec['name']}: binds folder {actual!r}, but the SDD "
                    f"resolves it to {E.TASK_RESOURCE[spec['name']]!r} in {expected!r}"
                )
    if problems:
        fail("task → resource pairing does not match §4:\n  - " + "\n  - ".join(problems))


def binding_groups(plan: dict) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for binding in plan.get("bindings") or []:
        key = binding.get("resourceKey")
        if isinstance(key, str):
            groups.setdefault(key, []).append(binding)
    return groups


def check_resource_key_consistency(plan: dict, groups: dict[str, list[dict]]) -> None:
    problems: list[str] = []
    for key, bindings in groups.items():
        if all(str(b.get("resource")) == "Connection" for b in bindings):
            continue
        defaults = {
            b.get("propertyAttribute"): b.get("default")
            for b in bindings
            if b.get("propertyAttribute")
        }
        name, folder = defaults.get("name"), defaults.get("folderPath")
        if name is None or folder is None:
            problems.append(
                f"{key!r}: a non-connector resource needs both a name and a folderPath "
                f"binding; propertyAttributes present: {sorted(defaults)}"
            )
            continue
        expected = f"{folder}.{name}"
        if key != expected:
            problems.append(
                f"{key!r}: resourceKey must be '<folderPath>.<name>' = {expected!r}"
            )
    if problems:
        fail(
            "resourceKey self-consistency (Step 12 Check 11) failed — `validate` does "
            "not catch this, it faults at case debug:\n  - " + "\n  - ".join(problems)
        )


def check_resource_coverage(plan: dict, groups: dict[str, list[dict]]) -> None:
    by_folder: dict[str, list[dict]] = {}
    for bindings in groups.values():
        for binding in bindings:
            if binding.get("propertyAttribute") == "folderPath":
                by_folder.setdefault(str(binding.get("default")), []).append(binding)

    missing = [
        f"{name} ({folder})"
        for name, folder in E.RESOURCE_FOLDERS.items()
        if folder not in by_folder
    ]
    if missing:
        fail(
            "no binding resolves these SDD resources to their deployment folder: "
            f"{missing}; folders bound: {sorted(by_folder)}"
        )

    names_by_folder: dict[str, set[str]] = {}
    for bindings in groups.values():
        folders = {
            str(b.get("default"))
            for b in bindings
            if b.get("propertyAttribute") == "folderPath"
        }
        names = {
            E.norm(b.get("default"))
            for b in bindings
            if b.get("propertyAttribute") == "name"
        }
        for folder in folders:
            names_by_folder.setdefault(folder, set()).update(names)
    wrong_name = [
        f"{name} (folder {E.RESOURCE_FOLDERS[name]} bound to "
        f"{sorted(names_by_folder.get(E.RESOURCE_FOLDERS[name], set()))})"
        for name in PINNED_NAMES
        if E.norm(name) not in names_by_folder.get(E.RESOURCE_FOLDERS[name], set())
    ]
    if wrong_name:
        fail(f"binding name default does not match the SDD resource name: {wrong_name}")

    wrong_contract: list[str] = []
    for name, kind in RESOURCE_KIND.items():
        folder = E.RESOURCE_FOLDERS[name]
        expected_resource, expected_sub = E.BINDING_CONTRACT[kind]
        for binding in by_folder.get(folder, []):
            actual_resource = binding.get("resource")
            actual_sub = binding.get("resourceSubType")
            if actual_resource != expected_resource or actual_sub != expected_sub:
                wrong_contract.append(
                    f"{name} ({kind}): expected resource={expected_resource!r} "
                    f"resourceSubType={expected_sub!r}, got resource={actual_resource!r} "
                    f"resourceSubType={actual_sub!r}"
                )
    if wrong_contract:
        fail(
            "binding resource / resourceSubType must follow the per-task-type table "
            "(plugins/variables/bindings/impl-json.md):\n  - "
            + "\n  - ".join(sorted(set(wrong_contract)))
        )


def check_connector_identities(plan: dict, caseplan_text: str) -> None:
    for label, guid in (
        ("connection ID", E.CONNECTION_ID),
        ("activity type ID", E.ACTIVITY_TYPE_ID),
    ):
        if guid not in caseplan_text:
            fail(f"the Outlook 365 {label} {guid} does not appear in caseplan.json")
    connection_bindings = [
        binding
        for binding in plan.get("bindings") or []
        if str(binding.get("resource")) == "Connection"
    ]
    if not connection_bindings:
        fail(
            "connector tasks bind through root bindings with resource 'Connection' "
            "(ConnectionId + folderKey); none found"
        )


def check_bindings_sidecar(plan: dict, groups: dict[str, list[dict]]) -> None:
    project_dir = os.path.dirname(E.CASEPLAN_PATH)
    path = os.path.join(project_dir, "bindings_v2.json")
    if not os.path.isfile(path):
        fail(f"bindings_v2.json missing next to caseplan.json (expected {path})")
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    try:
        sidecar = json.loads(text)
    except ValueError as exc:
        fail(f"bindings_v2.json is not valid JSON: {exc}")
    resources = sidecar.get("resources") or []
    if not resources:
        fail("bindings_v2.json has no resources[] entries")
    sidecar_keys = {
        E.norm(resource.get("key")) for resource in resources if resource.get("key")
    }
    expected_keys = {
        E.norm(key)
        for key, bindings in groups.items()
        if not all(str(b.get("resource")) == "Connection" for b in bindings)
    }
    missing = sorted(expected_keys - sidecar_keys)
    if missing:
        fail(
            "bindings_v2.json is out of parity with caseplan bindings (Step 12 Check 7) "
            f"— missing key(s): {missing}"
        )
    if E.CONNECTION_ID not in text.lower():
        fail(
            f"bindings_v2.json does not carry the Outlook 365 connection {E.CONNECTION_ID}"
        )


def main() -> None:
    plan = load_plan()
    with open(E.CASEPLAN_PATH, encoding="utf-8") as handle:
        caseplan_text = handle.read().lower()
    groups = binding_groups(plan)
    check_resolved(plan)
    check_task_resource_pairing(plan)
    check_resource_key_consistency(plan, groups)
    check_resource_coverage(plan, groups)
    check_connector_identities(plan, caseplan_text)
    check_bindings_sidecar(plan, groups)
    print(
        "OK: all 39 tasks resolved; 20 SDD resources bound by folder with consistent "
        "resourceKeys and per-type resource/resourceSubType; Outlook 365 connection "
        "and activity type present in caseplan.json and bindings_v2.json"
    )


if __name__ == "__main__":
    main()
