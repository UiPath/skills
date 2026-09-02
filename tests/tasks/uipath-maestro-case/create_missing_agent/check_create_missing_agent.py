#!/usr/bin/env python3
"""Verify inline agent creation, validation, registration, and case I/O wiring."""

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

CASE_NAME = "CreateMissingAgentCase"
RESOURCE_NAME = "InlineGreetingAgentQ74"
CASEPLAN = Path(CASE_NAME) / CASE_NAME / "caseplan.json"
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
    task = one(find_tasks_of_type(plan, "agent"), "agent task")
    if task_is_skeleton(task):
        fail("agent task is an unresolved skeleton")

    data = task.get("data") or {}
    name_binding = resolve_binding(plan, data.get("name"), "name")
    folder_binding = resolve_binding(plan, data.get("folderPath"), "folderPath")
    expected_key = f"solution_folder.{RESOURCE_NAME}"
    for binding in (name_binding, folder_binding):
        if binding.get("resource") != "process":
            fail(f"inline agent binding resource is {binding.get('resource')!r}")
        if binding.get("resourceSubType") != "Agent":
            fail(
                "inline agent binding resourceSubType is "
                f"{binding.get('resourceSubType')!r}"
            )
        if binding.get("resourceKey") != expected_key:
            fail(
                f"inline agent resourceKey is {binding.get('resourceKey')!r}, "
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
    greeting_var = case_variable(plan, "greeting")
    customer_id = customer_var.get("id")
    greeting_id = greeting_var.get("id")
    if not customer_id or not greeting_id:
        fail("customerName/greeting case variables must each have an id")

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
    if output_row.get("var") != greeting_id:
        fail(
            f"greeting output var is {output_row.get('var')!r}, "
            f"expected case variable id {greeting_id!r}"
        )
    if output_row.get("originalVar") != "greeting":
        fail("greeting extraction is missing originalVar='greeting'")


def assert_sibling_contract() -> None:
    project = load_json(SIBLING / "project.uiproj")
    if project.get("ProjectType") != "Agent":
        fail(f"sibling ProjectType is {project.get('ProjectType')!r}, expected 'Agent'")
    if not list(SIBLING.rglob("agent.json")):
        fail(f"no agent.json found under {SIBLING}")

    entry_points = load_json(SIBLING / "entry-points.json")
    entry = one(entry_points.get("entryPoints") or [], "agent entry point")
    input_schema = entry.get("input") or {}
    output_schema = entry.get("output") or {}
    input_props = input_schema.get("properties") or {}
    output_props = output_schema.get("properties") or {}
    if (input_props.get("customerName") or {}).get("type") != "string":
        fail("agent entry point does not expose customerName:string")
    if "customerName" not in (input_schema.get("required") or []):
        fail("agent entry point does not require customerName")
    if (output_props.get("greeting") or {}).get("type") != "string":
        fail("agent entry point does not expose greeting:string")

    solution = load_json(SOLUTION)
    projects = solution.get("Projects") or []
    expected_suffix = f"{RESOURCE_NAME}/project.uiproj"
    matches = [
        project
        for project in projects
        if str(project.get("ProjectRelativePath", "")).replace("\\", "/").endswith(expected_suffix)
    ]
    registered = one(matches, f"solution project ending in {expected_suffix!r}")
    if registered.get("Type") != "Agent":
        fail(f"registered sibling Type is {registered.get('Type')!r}")

    audit_path = Path("tasks/registry-resolved.json")
    audit_text = audit_path.read_text().lower() if audit_path.is_file() else ""
    if RESOURCE_NAME.lower() not in audit_text or '"local"' not in audit_text:
        fail("registry-resolved.json does not record the local inline agent")


def assert_sibling_validates() -> None:
    result = subprocess.run(
        ["uip", "agent", "validate", str(SIBLING), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        fail(
            f"inline agent validation exit {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        fail(f"inline agent validation returned invalid JSON: {exc}")
    data = payload.get("Data") or {}
    if payload.get("Result") != "Success" or data.get("Status") != "Valid":
        fail(f"inline agent validation did not report Valid: {payload!r}")


def main() -> None:
    plan = read_caseplan(str(CASEPLAN))
    assert_tasks_nested(plan)
    assert_validate_passes(str(CASEPLAN))
    assert_case_wiring(plan)
    assert_sibling_contract()
    assert_sibling_validates()
    print(
        "OK: missing agent created inline, customerName:string -> "
        "greeting:string is wired, and the sibling agent validates"
    )


if __name__ == "__main__":
    main()
