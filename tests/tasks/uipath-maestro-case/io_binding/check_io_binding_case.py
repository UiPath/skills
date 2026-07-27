#!/usr/bin/env python3
"""Grade the general task I/O binding matrix and equal-name regression."""

from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    _get_ci,
    assert_tasks_nested,
    find_tasks_of_type,
    first_rule_of_condition,
    read_caseplan,
    run_debug,
    task_is_skeleton,
)

RESOURCE_NAME = "API Workflow"
GOLDEN_FOLDER = "Shared/uipath-maestro-case/CM-Golden-Expense-Reporting-106"
GOLDEN_RESOURCE_KEY = f"{GOLDEN_FOLDER}.{RESOURCE_NAME}"
AGE_FOLDER = "Shared/uipath-maestro-case/NameToAgeFixed2"
AGE_RESOURCE_KEY = f"{AGE_FOLDER}.{RESOURCE_NAME}"

GOLDEN_TASKS = (
    "Echo literal",
    "Echo case variable",
    "Echo prior output",
    "Echo expression",
    "Consume colliding output",
    "Consume custom output",
)
AGE_TASKS = (
    "Lookup exact same name",
    "Lookup colliding same name",
)


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def one(items: list[dict], what: str) -> dict:
    if len(items) != 1:
        fail(f"expected exactly one {what}, got {len(items)}")
    return items[0]


def task_by_name(tasks: list[dict], name: str) -> dict:
    return one(
        [task for task in tasks if task.get("displayName") == name],
        f"api-workflow task named {name!r}",
    )


def variable(plan: dict, group: str, name: str) -> dict:
    return one(
        [
            item
            for item in (plan.get("variables") or {}).get(group) or []
            if item.get("name") == name
        ],
        f"variables.{group} entry named {name!r}",
    )


def resolve_binding(plan: dict, reference: object, property_name: str) -> dict:
    prefix = "=bindings."
    if not isinstance(reference, str) or not reference.startswith(prefix):
        fail(f"task data.{property_name} is not a binding reference: {reference!r}")
    binding_id = reference[len(prefix) :]
    binding = one(
        [item for item in plan.get("bindings") or [] if item.get("id") == binding_id],
        f"binding {binding_id!r}",
    )
    if binding.get("propertyAttribute") != property_name:
        fail(
            f"binding {binding_id!r} propertyAttribute is "
            f"{binding.get('propertyAttribute')!r}, expected {property_name!r}"
        )
    return binding


def assert_resource_binding(
    plan: dict, task: dict, *, folder: str, resource_key: str
) -> tuple[str, str]:
    data = task.get("data") or {}
    name_binding = resolve_binding(plan, data.get("name"), "name")
    folder_binding = resolve_binding(plan, data.get("folderPath"), "folderPath")
    for binding in (name_binding, folder_binding):
        if binding.get("resource") != "process":
            fail(f"API binding resource is {binding.get('resource')!r}")
        if binding.get("resourceSubType") != "Api":
            fail(f"API binding resourceSubType is {binding.get('resourceSubType')!r}")
        if binding.get("resourceKey") != resource_key:
            fail(
                f"API binding resourceKey is {binding.get('resourceKey')!r}, "
                f"expected {resource_key!r}"
            )
        if str(binding.get("resourceKey", "")).startswith("solution_folder."):
            fail("task binds an inline solution sibling instead of a tenant API workflow")
    if name_binding.get("default") != RESOURCE_NAME:
        fail(
            f"name binding default is {name_binding.get('default')!r}, "
            f"expected {RESOURCE_NAME!r}"
        )
    if folder_binding.get("default") != folder:
        fail(
            f"folder binding default is {folder_binding.get('default')!r}, "
            f"expected {folder!r}"
        )
    return name_binding["id"], folder_binding["id"]


def assert_solution_shape() -> None:
    manifests = glob.glob("**/*.uipx", recursive=True)
    if len(manifests) != 1:
        fail(f"expected one solution manifest, got {manifests}")
    with open(manifests[0], encoding="utf-8") as stream:
        solution = json.load(stream)
    api_projects = [
        project
        for project in solution.get("Projects") or []
        if str(project.get("Type", "")).lower() == "api"
    ]
    if api_projects:
        fail("solution contains an inline API project instead of tenant resources")
    case_projects = [
        project
        for project in solution.get("Projects") or []
        if project.get("Type") == "CaseManagement"
    ]
    if len(case_projects) != 1:
        fail(
            "solution must register exactly one CaseManagement project, got "
            f"{len(case_projects)}"
        )


def input_row(task: dict, name: str) -> dict:
    return one(
        [row for row in (task.get("data") or {}).get("inputs") or [] if row.get("name") == name],
        f"input {name!r} on task {task.get('displayName')!r}",
    )


def output_row(task: dict, *, name: str | None = None, source: str | None = None) -> dict:
    rows = (task.get("data") or {}).get("outputs") or []
    if name is not None:
        rows = [row for row in rows if row.get("name") == name]
    if source is not None:
        rows = [row for row in rows if row.get("source") == source]
    label = name if name is not None else source
    return one(rows, f"output {label!r} on task {task.get('displayName')!r}")


def assert_bare_output(task: dict, name: str, output_type: str) -> dict:
    output = output_row(task, name=name)
    output_id = output.get("id")
    expected = {
        "type": output_type,
        "var": output_id,
        "value": output_id,
        "source": f"={name}",
        "target": f"={output_id}",
    }
    mismatches = {
        key: {"expected": value, "actual": output.get(key)}
        for key, value in expected.items()
        if output.get(key) != value
    }
    if not isinstance(output_id, str) or not output_id:
        mismatches["id"] = {"expected": "non-empty string", "actual": output_id}
    if "originalVar" in output:
        mismatches["originalVar"] = {"expected": "absent", "actual": output.get("originalVar")}
    if mismatches:
        fail(f"bare output {name!r} is not canonical: {mismatches}")
    return output


def assert_reassigned_output(
    task: dict,
    *,
    source: str,
    target_var: str,
    output_type: str,
    expected_id: str | None = None,
    expected_name: str | None = None,
) -> dict:
    output = output_row(task, source=f"={source}")
    output_id = output.get("id")
    expected_output_id = expected_id if expected_id is not None else output_id
    expected = {
        "type": output_type,
        "var": target_var,
        "value": target_var,
        "source": f"={source}",
        "target": f"={expected_output_id}",
        "originalVar": expected_output_id,
    }
    if expected_id is not None:
        expected["id"] = expected_id
    if expected_name is not None:
        expected["name"] = expected_name
    mismatches = {
        key: {"expected": value, "actual": output.get(key)}
        for key, value in expected.items()
        if output.get(key) != value
    }
    if not isinstance(output_id, str) or not output_id:
        mismatches["id"] = {"expected": "non-empty string", "actual": output_id}
    if mismatches:
        fail(
            f"reassigned output {source!r} -> {target_var!r} "
            f"is not canonical: {mismatches}"
        )
    return output


def assert_custom_output(
    task: dict, name: str, value: str, output_type: str = "string"
) -> dict:
    output = output_row(task, name=name)
    expected = {
        "custom": True,
        "var": name,
        "value": value,
        "source": value,
        "target": "",
        "body": "",
        "type": output_type,
        "elementId": "root",
    }
    mismatches = {
        key: {"expected": expected_value, "actual": output.get(key)}
        for key, expected_value in expected.items()
        if output.get(key) != expected_value
    }
    for forbidden in ("id", "originalVar"):
        if forbidden in output:
            mismatches[forbidden] = {"expected": "absent", "actual": output.get(forbidden)}
    if mismatches:
        fail(f"custom output {name!r} is not canonical: {mismatches}")
    return output


def assert_selected_after(task: dict, predecessor: dict) -> None:
    rules = [
        first_rule_of_condition(condition)
        for condition in task.get("entryConditions") or []
    ]
    matching = [rule for rule in rules if rule and rule.get("rule") == "selected-tasks-completed"]
    rule = one(matching, f"selected-tasks-completed entry rule on {task.get('displayName')!r}")
    selected_ids = rule.get("selectedTasksIds") or []
    if selected_ids != [predecessor.get("id")]:
        fail(
            f"task {task.get('displayName')!r} must run after "
            f"{predecessor.get('displayName')!r}; got selectedTasksIds={selected_ids}"
        )


def assert_runtime_tasks_completed(payload: dict, tasks: tuple[dict, ...]) -> None:
    """Case debug exposes execution telemetry, not runtime variable snapshots."""
    executions = _get_ci(payload, "elementExecutions", "ElementExecutions", default=[]) or []
    for task in tasks:
        task_id = task.get("id")
        matching = [
            item
            for item in executions
            if _get_ci(item, "elementId", "ElementId") == task_id
        ]
        execution = one(matching, f"debug execution for task {task.get('displayName')!r}")
        status = _get_ci(execution, "status", "Status")
        if status not in ("Completed", "Successful"):
            fail(
                f"debug execution for task {task.get('displayName')!r} "
                f"finished with status {status!r}"
            )


def assert_sdd_output_contract() -> None:
    if not os.path.isfile("sdd.md"):
        fail("missing sdd.md")
    with open("sdd.md", encoding="utf-8") as stream:
        lines = stream.readlines()

    in_outputs = False
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r"^\*\*Outputs:?\*\*$", stripped):
            in_outputs = True
            continue
        if in_outputs and stripped.startswith(("#", "**Inputs")):
            in_outputs = False
        if not in_outputs or not stripped.startswith("|"):
            continue

        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 3:
            continue
        field, _output_type, binding = cells
        if field == "Field" or (field and set(field) <= {"-", ":"}):
            continue
        if binding.startswith("->"):
            if field in ("", "—"):
                fail(f"sdd.md:{line_number} extract output is missing its Field")
            if not binding[2:].strip():
                fail(f"sdd.md:{line_number} extract output is missing its target")
            continue
        assignment = re.match(
            r"^[A-Za-z_][A-Za-z0-9_]*\s*=(?!=)\s*(.+)$", binding
        )
        if assignment:
            if field not in ("", "—"):
                fail(f"sdd.md:{line_number} assignment output has a non-empty Field")
            continue
        fail(
            f"sdd.md:{line_number} output row has no supported `->` or `=` "
            f"binding: {stripped}"
        )


def assert_tasks_md() -> None:
    tasks_path = "tasks/tasks.md"
    if not os.path.isfile(tasks_path):
        fail("missing tasks/tasks.md")
    with open(tasks_path, encoding="utf-8") as stream:
        text = stream.read()

    leaked_field_placeholder = re.compile(r"^\s*-\s*—\s*=.*$", re.MULTILINE)
    leaked = leaked_field_placeholder.search(text)
    if leaked:
        fail(
            "tasks.md leaked an SDD Field placeholder/operator into an output "
            f"item: {leaked.group(0).strip()!r}; expected `<case-variable> = "
            "<expression>` for assignment rows"
        )

    expected_rows = (
        r"APIOutput1\s*->\s*renamedResult",
        r"Error\.Message\s*->\s*errorMessage",
        r'literalResult\s*=\s*"literal-assigned"',
        r"copiedResult\s*=\s*=vars\.renamedResult",
        r"computedResult\s*=\s*=js:vars\.\$xref\('Binding Matrix','Echo literal','APIOutput1'\)\s*\+\s*'-computed'",
        r"metadataResult\s*=\s*=metadata\.ExternalId",
        r"APIInput1\s*<-\s*\"Binding Matrix\"\.\"Lookup colliding same name\"\.estimatedAge",
        r"collisionCopy\s*=\s*=js:vars\.\$xref\('Binding Matrix','Lookup colliding same name','estimatedAge'\)\s*\+\s*0",
        r"APIInput1\s*<-\s*\"Binding Matrix\"\.\"Consume colliding output\"\.collisionCopy",
        r"customReferenceCopy\s*=\s*=js:vars\.\$xref\('Binding Matrix','Consume colliding output','collisionCopy'\)\s*\+\s*0",
    )
    for pattern in expected_rows:
        if not re.search(rf"^\s*-\s*(?:outputs:\s*)?{pattern}\s*$", text, re.MULTILINE):
            fail(f"tasks.md did not preserve row matching {pattern!r}")

    bare = re.compile(r"^\s*-\s*(?:outputs:\s*)?APIOutput1\s*$", re.MULTILINE)
    if not bare.search(text):
        fail("tasks.md is missing a bare `APIOutput1` auto-mint output")

    equal_name = re.compile(
        r"^\s*-\s*(?:outputs:\s*)?estimatedAge\s*->\s*estimatedAge\s*$",
        re.MULTILINE,
    )
    if len(equal_name.findall(text)) != 2:
        fail("tasks.md must preserve both `estimatedAge -> estimatedAge` rows")


def assert_variable_contract(plan: dict) -> None:
    formal_input = variable(plan, "inputs", "caseInput")
    if not str(formal_input.get("id", "")).startswith("v"):
        fail(f"caseInput formal input id must be letter-leading v*: {formal_input.get('id')!r}")
    input_companion = variable(plan, "inputOutputs", "caseInput")
    if input_companion.get("id") != "caseInput":
        fail(f"caseInput companion id is {input_companion.get('id')!r}")

    for name in ("renamedResult", "errorMessage", "estimatedAge"):
        companion = variable(plan, "inputOutputs", name)
        if companion.get("id") != name:
            fail(f"{name} companion id is {companion.get('id')!r}")

    for name in (
        "literalResult",
        "copiedResult",
        "computedResult",
        "metadataResult",
        "collisionCopy",
        "customReferenceCopy",
    ):
        formal_output = variable(plan, "outputs", name)
        companion = variable(plan, "inputOutputs", name)
        if formal_output.get("var") != name:
            fail(f"{name} formal output var is {formal_output.get('var')!r}")
        if companion.get("id") != name:
            fail(f"{name} companion id is {companion.get('id')!r}")


def main() -> None:
    assert_sdd_output_contract()
    plan = read_caseplan()
    assert_tasks_nested(plan)
    tasks = find_tasks_of_type(plan, "api-workflow")
    if len(tasks) != 8:
        fail(f"expected eight api-workflow tasks, got {len(tasks)}")
    for task in tasks:
        if task_is_skeleton(task):
            fail(f"api-workflow task {task.get('displayName')!r} is an unresolved skeleton")
        if task.get("shouldRunOnlyOnce") is not True:
            fail(f"api-workflow task {task.get('displayName')!r} must run only once")

    golden = [task_by_name(tasks, name) for name in GOLDEN_TASKS]
    ages = [task_by_name(tasks, name) for name in AGE_TASKS]

    golden_binding_pairs = {
        assert_resource_binding(
            plan, task, folder=GOLDEN_FOLDER, resource_key=GOLDEN_RESOURCE_KEY
        )
        for task in golden
    }
    if len(golden_binding_pairs) != 1:
        fail(f"Golden tasks did not deduplicate their name/folder bindings: {golden_binding_pairs}")
    age_binding_pairs = {
        assert_resource_binding(
            plan, task, folder=AGE_FOLDER, resource_key=AGE_RESOURCE_KEY
        )
        for task in ages
    }
    if len(age_binding_pairs) != 1:
        fail(f"NameToAge tasks did not deduplicate their bindings: {age_binding_pairs}")
    if age_binding_pairs & golden_binding_pairs:
        fail("Golden and NameToAge tasks incorrectly share one binding pair")
    if len(plan.get("bindings") or []) != 4:
        fail(f"expected exactly four deduplicated API bindings, got {len(plan.get('bindings') or [])}")
    assert_solution_shape()
    assert_variable_contract(plan)

    literal, case_var, prior, expression, consumer, custom_consumer = golden
    bare_output = assert_bare_output(literal, "APIOutput1", "string")
    if input_row(literal, "APIInput1").get("value") != "literal-seed":
        fail(f"literal APIInput1 is {input_row(literal, 'APIInput1').get('value')!r}")

    if input_row(case_var, "APIInput1").get("value") != "=vars.caseInput":
        fail(f"case-variable APIInput1 is {input_row(case_var, 'APIInput1').get('value')!r}")
    assert_reassigned_output(
        case_var, source="APIOutput1", target_var="renamedResult", output_type="string"
    )
    assert_reassigned_output(
        case_var,
        source="Error.Message",
        target_var="errorMessage",
        output_type="string",
        expected_name="Message",
    )
    case_var_outputs = (case_var.get("data") or {}).get("outputs") or []
    if any(row.get("source") == "=Error" for row in case_var_outputs):
        fail(
            "nested Error.Message extraction must not also auto-mint "
            "the parent Error output"
        )

    expected_cross_task = f"=vars.{bare_output['id']}"
    if input_row(prior, "APIInput1").get("value") != expected_cross_task:
        fail(
            f"cross-task APIInput1 is {input_row(prior, 'APIInput1').get('value')!r}, "
            f"expected {expected_cross_task!r}"
        )
    assert_custom_output(prior, "literalResult", "literal-assigned")
    assert_custom_output(prior, "copiedResult", "=vars.renamedResult")
    assert_custom_output(
        prior,
        "computedResult",
        f"=js:vars.{bare_output['id']} + '-computed'",
    )

    expression_value = "=js:vars.renamedResult + '-input-expression'"
    if input_row(expression, "APIInput1").get("value") != expression_value:
        fail(
            f"expression APIInput1 is {input_row(expression, 'APIInput1').get('value')!r}, "
            f"expected {expression_value!r}"
        )
    assert_custom_output(expression, "metadataResult", "=js:metadata.ExternalId")

    first_age, colliding_age = ages
    for age in ages:
        if input_row(age, "name").get("value") != "=vars.caseInput":
            fail(
                f"age lookup input on {age.get('displayName')!r} is "
                f"{input_row(age, 'name').get('value')!r}"
            )
    assert_reassigned_output(
        first_age,
        source="estimatedAge",
        target_var="estimatedAge",
        output_type="number",
        expected_id="estimatedAge",
    )
    colliding_output = assert_reassigned_output(
        colliding_age,
        source="estimatedAge",
        target_var="estimatedAge",
        output_type="number",
        expected_id="estimatedAge2",
    )

    expected_colliding_ref = f"=vars.{colliding_output['id']}"
    if input_row(consumer, "APIInput1").get("value") != expected_colliding_ref:
        fail(
            f"colliding-output consumer APIInput1 is "
            f"{input_row(consumer, 'APIInput1').get('value')!r}, "
            f"expected source output id reference {expected_colliding_ref!r}"
        )
    assert_custom_output(
        consumer,
        "collisionCopy",
        f"=js:vars.{colliding_output['id']} + 0",
        output_type="number",
    )

    expected_custom_ref = "=vars.collisionCopy"
    if input_row(custom_consumer, "APIInput1").get("value") != expected_custom_ref:
        fail(
            f"custom-output consumer APIInput1 is "
            f"{input_row(custom_consumer, 'APIInput1').get('value')!r}, "
            f"expected root companion reference {expected_custom_ref!r}"
        )
    assert_custom_output(
        custom_consumer,
        "customReferenceCopy",
        "=js:vars.collisionCopy + 0",
        output_type="number",
    )

    chain = (
        literal,
        case_var,
        prior,
        expression,
        first_age,
        colliding_age,
        consumer,
        custom_consumer,
    )
    for predecessor, task in zip(chain, chain[1:]):
        assert_selected_after(task, predecessor)

    if "$xref(" in json.dumps(plan):
        fail("caseplan.json still contains an unresolved $xref marker")
    all_output_ids = [
        row.get("id")
        for task in tasks
        for row in (task.get("data") or {}).get("outputs") or []
        if row.get("id")
    ]
    if len(all_output_ids) != len(set(all_output_ids)):
        fail(f"task output ids are not globally unique: {all_output_ids}")
    assert_tasks_md()

    payload = run_debug(timeout=900)
    assert_runtime_tasks_completed(payload, chain)
    print(
        "OK: Golden Expense API covers the general I/O binding matrix; "
        "NameToAge preserves equal-name reassignment and deduplicates an "
        "unrelated task-output collision; custom-output references resolve "
        "through the root companion; debug completed"
    )


if __name__ == "__main__":
    main()
