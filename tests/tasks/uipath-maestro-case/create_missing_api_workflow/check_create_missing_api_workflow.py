#!/usr/bin/env python3
"""Verify inline API creation, validation, registration, and case I/O wiring."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CASE_TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CASE_TASK_ROOT))

from _shared.case_check import (  # noqa: E402
    assert_tasks_nested,
    assert_validate_passes,
    find_tasks_of_type,
    read_caseplan,
    task_is_skeleton,
)

CASE_NAME = "CreateMissingApiWorkflowCase"
RESOURCE_NAME = "InlineGreetingApiQ74"
SOLUTION = Path(CASE_NAME) / f"{CASE_NAME}.uipx"
SIBLING = Path(CASE_NAME) / RESOURCE_NAME


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")


def one(items: list[dict], what: str) -> dict:
    if len(items) != 1:
        fail(f"expected exactly one {what}, got {len(items)}")
    return items[0]


def resolve_caseplan(solution: dict) -> Path:
    case_project = one(
        [
            project
            for project in solution.get("Projects") or []
            if project.get("Type") == "CaseManagement"
        ],
        "CaseManagement solution project",
    )
    relative_path = case_project.get("ProjectRelativePath")
    if not isinstance(relative_path, str) or not relative_path:
        fail("CaseManagement project is missing ProjectRelativePath")
    project_path = Path(CASE_NAME) / Path(relative_path.replace("\\", "/"))
    if project_path.name != "project.uiproj":
        fail(
            "CaseManagement ProjectRelativePath must end in project.uiproj, got "
            f"{relative_path!r}"
        )
    return project_path.parent / "caseplan.json"


def case_variable(plan: dict, name: str) -> dict:
    variables = plan.get("variables") or {}
    matches = [
        item
        for group in ("inputs", "outputs", "inputOutputs")
        for item in variables.get(group) or []
        if item.get("name") == name
    ]
    return one(matches, f"case variable named {name!r}")


def resolve_binding(plan: dict, reference: object, property_name: str) -> dict:
    prefix = "=bindings."
    if not isinstance(reference, str) or not reference.startswith(prefix):
        fail(f"task data.{property_name} is not a binding reference: {reference!r}")
    binding_id = reference[len(prefix) :]
    matches = [b for b in plan.get("bindings") or [] if b.get("id") == binding_id]
    binding = one(matches, f"binding {binding_id!r}")
    if binding.get("propertyAttribute") != property_name:
        fail(
            f"binding {binding_id!r} propertyAttribute is "
            f"{binding.get('propertyAttribute')!r}, expected {property_name!r}"
        )
    return binding


def assert_case_wiring(plan: dict) -> None:
    task = one(find_tasks_of_type(plan, "api-workflow"), "api-workflow task")
    if task_is_skeleton(task):
        fail("api-workflow task is an unresolved skeleton")

    data = task.get("data") or {}
    name_binding = resolve_binding(plan, data.get("name"), "name")
    folder_binding = resolve_binding(plan, data.get("folderPath"), "folderPath")
    expected_key = f"solution_folder.{RESOURCE_NAME}"
    for binding in (name_binding, folder_binding):
        if binding.get("resource") != "process":
            fail(f"inline API binding resource is {binding.get('resource')!r}")
        if binding.get("resourceSubType") != "Api":
            fail(
                "inline API binding resourceSubType is "
                f"{binding.get('resourceSubType')!r}"
            )
        if binding.get("resourceKey") != expected_key:
            fail(
                f"inline API resourceKey is {binding.get('resourceKey')!r}, "
                f"expected {expected_key!r}"
            )
    if name_binding.get("default") != RESOURCE_NAME:
        fail(f"name binding default is {name_binding.get('default')!r}")
    if folder_binding.get("default") != "":
        fail(
            "inline sibling folderPath must be the co-located empty string, got "
            f"{folder_binding.get('default')!r}"
        )

    customer_var = case_variable(plan, "customerName")
    greeting_in_var = case_variable(plan, "greetingIn")
    customer_id = customer_var.get("id")
    greeting_in_id = greeting_in_var.get("id")
    if not customer_id or not greeting_in_id:
        fail("customerName/greetingIn case variables must each have an id")

    input_row = one(
        [row for row in data.get("inputs") or [] if row.get("name") == "customerName"],
        "customerName task input",
    )
    if input_row.get("type") != "string":
        fail(f"customerName task input type is {input_row.get('type')!r}")
    if input_row.get("value") != f"=vars.{customer_id}":
        fail(
            f"customerName input is {input_row.get('value')!r}, "
            f"expected '=vars.{customer_id}'"
        )

    output_row = one(
        [row for row in data.get("outputs") or [] if row.get("name") == "greeting"],
        "greeting task output",
    )
    if output_row.get("type") != "string":
        fail(f"greeting task output type is {output_row.get('type')!r}")
    if output_row.get("source") != "=greeting":
        fail(f"greeting output source is {output_row.get('source')!r}")
    if output_row.get("var") != greeting_in_id:
        fail(
            f"greeting output var is {output_row.get('var')!r}, "
            f"expected greetingIn case variable id {greeting_in_id!r}"
        )
    if output_row.get("originalVar") != "greeting":
        fail("greeting extraction is missing originalVar='greeting'")


def assert_sibling_contract(solution: dict) -> Path:
    project = load_json(SIBLING / "project.uiproj")
    if project.get("ProjectType") != "Api":
        fail(f"sibling ProjectType is {project.get('ProjectType')!r}, expected 'Api'")
    workflow_files = list(SIBLING.rglob("Workflow.json"))
    workflow = Path(one([{"path": str(p)} for p in workflow_files], "Workflow.json")["path"])

    entry_points = load_json(SIBLING / "entry-points.json")
    entry = one(entry_points.get("entryPoints") or [], "API workflow entry point")
    input_schema = entry.get("input") or {}
    output_schema = entry.get("output") or {}
    input_props = input_schema.get("properties") or {}
    output_props = output_schema.get("properties") or {}
    if (input_props.get("customerName") or {}).get("type") != "string":
        fail("API entry point does not expose customerName:string in the flat schema")
    if "customerName" not in (input_schema.get("required") or []):
        fail("API entry point does not require customerName")
    if (output_props.get("greeting") or {}).get("type") != "string":
        fail("API entry point does not expose greeting:string in the flat schema")

    projects = solution.get("Projects") or []
    expected_suffix = f"{RESOURCE_NAME}/project.uiproj"
    matches = [
        project
        for project in projects
        if str(project.get("ProjectRelativePath", "")).replace("\\", "/").endswith(expected_suffix)
    ]
    registered = one(matches, f"solution project ending in {expected_suffix!r}")
    if registered.get("Type") != "Api":
        fail(f"registered sibling Type is {registered.get('Type')!r}")

    audit_path = Path("tasks/registry-resolved.json")
    audit_text = audit_path.read_text().lower() if audit_path.is_file() else ""
    if RESOURCE_NAME.lower() not in audit_text or '"local"' not in audit_text:
        fail("registry-resolved.json does not record the local inline API workflow")
    return workflow


def assert_workflow_valid(workflow: Path) -> None:
    result = subprocess.run(
        ["uip", "api-workflow", "validate", str(workflow), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        fail(
            f"uip api-workflow validate exit {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    if "valid" not in result.stdout.lower():
        fail(f"API workflow validation did not report Valid: {result.stdout[:1000]}")


def load_and_validate_case() -> tuple[dict, dict]:
    solution = load_json(SOLUTION)
    caseplan = resolve_caseplan(solution)
    plan = read_caseplan(str(caseplan))
    assert_tasks_nested(plan)
    assert_validate_passes(str(caseplan))
    return plan, solution


def main() -> None:
    plan, solution = load_and_validate_case()
    if sys.argv[1:] == ["--case-only"]:
        print(
            "OK: discovered CaseManagement project from the solution and "
            "validated its caseplan"
        )
        return
    if sys.argv[1:]:
        fail("usage: check_create_missing_api_workflow.py [--case-only]")
    assert_case_wiring(plan)
    workflow = assert_sibling_contract(solution)
    assert_workflow_valid(workflow)
    print(
        "OK: missing API workflow created inline, customerName:string -> "
        "greeting:string -> greetingIn:string is wired, and the sibling API "
        "workflow validates"
    )


if __name__ == "__main__":
    main()
