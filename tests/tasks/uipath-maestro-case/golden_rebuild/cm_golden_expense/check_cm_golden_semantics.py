#!/usr/bin/env python3
"""CM-Golden rebuild: deterministic dataflow and condition grader.

The case builder lowers SDD ``vars.$xref(stage, task, output)`` expressions to
``vars.<output-id>`` references, where task/stage IDs are minted per build.
This checker resolves those IDs back to logical names and verifies the semantic
contract that previously depended on an LLM judge:

  - every SDD-bound task input uses the expected upstream task output
  - every consumed ``vars.<id>`` has a real producer
  - behavior-bearing literal inputs and action recipients survive
  - every stage/task entry and exit condition has the expected rule + target
  - Stage 2 reject and Stage 4 approve/reject gates use the correct output,
    polarity, exit type, and completion behavior
"""

from __future__ import annotations

from collections import Counter
import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import find_stages, read_caseplan  # noqa: E402

EXPECTED_CASEPLAN = os.path.join("CMGoldenExpense", "CMGoldenExpense", "caseplan.json")
FIXTURE_SDD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "sdd.md")

TASKS_BY_STAGE = {
    "Stage 1": [
        "Analyze Expense Request",
        "Process Expense Request",
        "Record Expense via RPA",
    ],
    "Stage 2": [
        "Manager Approval",
        "Wait for timer - S2 run once",
        "Call Expense API",
        "Wait for timer - S2 adhoc",
    ],
    "Stage 3": ["Wait for HTTP Webhook", "List Emails", "Start Child Case"],
    "Stage 4": ["Rework Approval"],
    "Stage 5": ["Wait for timer - S5"],
    "Stage 6": ["Timer to be interrupted"],
    "Stage 7": ["Wait for timer - S7"],
    "Stage 8": ["Wait for timer - S8"],
}

VAR_REF_RE = re.compile(r"\bvars\.([A-Za-z_][A-Za-z0-9_]*)")
GATE_RE = re.compile(
    r"^\s*=js:\s*vars\.([A-Za-z_][A-Za-z0-9_]*)\s*"
    r"===\s*(['\"])(approve|reject)\2\s*$"
)
OUTLOOK_FOLDER_ID_RE = re.compile(r"^(?:AAMk|AQMk)[A-Za-z0-9+/_=-]{28,}$")


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _read_plan() -> dict:
    if len(sys.argv) > 1:
        return read_caseplan(sys.argv[1])
    if os.path.exists(EXPECTED_CASEPLAN):
        return read_caseplan(EXPECTED_CASEPLAN)
    return read_caseplan()


def _expected_recipient() -> dict:
    try:
        with open(FIXTURE_SDD, encoding="utf-8") as stream:
            sdd = stream.read()
    except OSError as exc:
        _fail(f"cannot read fixture SDD {FIXTURE_SDD}: {exc}")
    recipients = set(re.findall(r"\*\*Recipient:\*\*\s*Email:\s*([^\s]+)", sdd))
    if len(recipients) != 1:
        _fail(
            "fixture parse error: expected one shared action recipient; "
            f"got {sorted(recipients)!r}"
        )
    return {"Type": 2, "Value": recipients.pop()}


def _stage_tasks(stage: dict) -> list[dict]:
    tasks: list[dict] = []
    for lane in ((stage.get("data") or {}).get("tasks") or []):
        if isinstance(lane, dict):
            tasks.append(lane)
        elif isinstance(lane, list):
            tasks.extend(task for task in lane if isinstance(task, dict))
    return tasks


def _index_plan(plan: dict):
    stages = find_stages(plan, include_exception=True)
    stage_by_key: dict[str, dict] = {}
    stage_id_to_key: dict[str, str] = {}

    for key in TASKS_BY_STAGE:
        matches = [
            stage
            for stage in stages
            if _norm((stage.get("data") or {}).get("label")).startswith(_norm(key))
        ]
        if len(matches) != 1:
            labels = [(stage.get("data") or {}).get("label") for stage in matches]
            _fail(f"expected one stage matching {key!r}; got {labels}")
        stage = matches[0]
        stage_by_key[key] = stage
        stage_id = stage.get("id")
        if not isinstance(stage_id, str) or not stage_id:
            _fail(f"stage {key!r} has no id")
        stage_id_to_key[stage_id] = key

    task_by_logical: dict[tuple[str, str], dict] = {}
    task_id_to_logical: dict[str, tuple[str, str]] = {}
    for stage_key, expected_names in TASKS_BY_STAGE.items():
        tasks = _stage_tasks(stage_by_key[stage_key])
        actual_names = [task.get("displayName") for task in tasks]
        if Counter(actual_names) != Counter(expected_names):
            _fail(
                f"stage {stage_key!r} task names {actual_names!r} "
                f"!= expected {expected_names!r}"
            )
        for task in tasks:
            logical = (stage_key, task["displayName"])
            task_by_logical[logical] = task
            task_id = task.get("id")
            if not isinstance(task_id, str) or not task_id:
                _fail(f"task {logical!r} has no id")
            if task_id in task_id_to_logical:
                _fail(f"duplicate task id {task_id!r}")
            task_id_to_logical[task_id] = logical

    output_by_logical: dict[tuple[str, str, str], dict] = {}
    output_id_to_logical: dict[str, tuple[str, str, str]] = {}
    for (stage_key, task_name), task in task_by_logical.items():
        for output in (task.get("data") or {}).get("outputs") or []:
            output_name = output.get("name")
            output_id = output.get("id")
            output_var = output.get("var")
            if not isinstance(output_name, str) or not output_name:
                _fail(f"task {(stage_key, task_name)!r} has an output without a name")
            if not isinstance(output_id, str) or not output_id:
                _fail(
                    f"output {(stage_key, task_name, output_name)!r} has no generated id"
                )
            if output_var != output_id:
                _fail(
                    f"output {(stage_key, task_name, output_name)!r} has "
                    f"id={output_id!r} but var={output_var!r}"
                )
            logical = (stage_key, task_name, output_name)
            if logical in output_by_logical:
                _fail(f"duplicate logical output {logical!r}")
            if output_id in output_id_to_logical:
                _fail(f"duplicate generated output id {output_id!r}")
            output_by_logical[logical] = output
            output_id_to_logical[output_id] = logical

    return (
        stage_by_key,
        stage_id_to_key,
        task_by_logical,
        task_id_to_logical,
        output_by_logical,
        output_id_to_logical,
    )


def _output_id(outputs: dict, logical: tuple[str, str, str]) -> str:
    output = outputs.get(logical)
    if output is None:
        _fail(f"required producer output missing: {logical!r}")
    return output["id"]


def _inputs(task: dict) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for item in (task.get("data") or {}).get("inputs") or []:
        name = item.get("name")
        if not isinstance(name, str) or not name:
            _fail(f"task {task.get('displayName')!r} has an input without a name")
        if name in found:
            _fail(f"task {task.get('displayName')!r} has duplicate input {name!r}")
        found[name] = item
    return found


def _input(task: dict, name: str) -> dict:
    item = _inputs(task).get(name)
    if item is None:
        _fail(f"task {task.get('displayName')!r} missing input {name!r}")
    return item


def _assert_source(value, kind: str, producer_id: str, where: str):
    if not isinstance(value, str):
        _fail(f"{where} must be an expression string; got {value!r}")
    escaped = re.escape(producer_id)
    patterns = {
        "direct": rf"^\s*=vars\.{escaped}\s*$",
        "json-stringify": (
            rf"^\s*=js:\s*JSON\.stringify\(\s*vars\.{escaped}\s*\)\s*$"
        ),
        "greeting": (
            rf"^\s*=js:\s*`Hi \$\{{JSON\.stringify\(\s*vars\.{escaped}\s*\)\}}`\s*$"
        ),
    }
    if not re.fullmatch(patterns[kind], value):
        _fail(
            f"{where} is wired as {value!r}; expected {kind} reference to "
            f"producer id {producer_id!r}"
        )


def _assert_dataflow(plan: dict, tasks: dict, outputs: dict, outputs_by_id: dict):
    expected_sources = [
        (
            ("Stage 1", "Process Expense Request"),
            "ProcessExpenseRequestIn",
            ("Stage 1", "Analyze Expense Request", "AgentExpenseRequest"),
            "direct",
        ),
        (
            ("Stage 1", "Record Expense via RPA"),
            "RPAExpenseRequestIn",
            ("Stage 1", "Process Expense Request", "ProcessExpenseRequestOut"),
            "json-stringify",
        ),
        (
            ("Stage 2", "Manager Approval"),
            "Content",
            ("Stage 1", "Analyze Expense Request", "AgentExpenseRequest"),
            "greeting",
        ),
        (
            ("Stage 2", "Manager Approval"),
            "Comment",
            ("Stage 1", "Record Expense via RPA", "RPAExpenseRequestOut"),
            "json-stringify",
        ),
        (
            ("Stage 2", "Call Expense API"),
            "APIInput1",
            ("Stage 2", "Manager Approval", "Comment"),
            "direct",
        ),
        (
            ("Stage 3", "Start Child Case"),
            "caseInput1",
            ("Stage 2", "Manager Approval", "Comment"),
            "json-stringify",
        ),
    ]
    expected_ref_locations: set[tuple[tuple[str, str], str]] = set()
    for consumer, input_name, producer, kind in expected_sources:
        producer_id = _output_id(outputs, producer)
        value = _input(tasks[consumer], input_name).get("value")
        _assert_source(value, kind, producer_id, f"{consumer!r} input {input_name!r}")
        expected_ref_locations.add((consumer, input_name))

    rework = tasks[("Stage 4", "Rework Approval")]
    for field in ("Content", "Comment"):
        value = _input(rework, field).get("value")
        if value != "":
            _fail(f"Rework Approval input {field!r} must be the SDD empty literal")

    webhook_body = _input(tasks[("Stage 3", "Wait for HTTP Webhook")], "body").get(
        "body"
    )
    if webhook_body not in ({}, None):
        _fail(f"Wait for HTTP Webhook body must be unbound; got {webhook_body!r}")

    email_inputs = _inputs(tasks[("Stage 3", "List Emails")])
    populated_parameter_sets = []
    for container_name in ("body", "queryParameters"):
        item = email_inputs.get(container_name) or {}
        parameters = item.get("body")
        if isinstance(parameters, dict) and parameters:
            populated_parameter_sets.append((container_name, parameters))
    if len(populated_parameter_sets) != 1:
        _fail(
            "List Emails must have exactly one populated body or "
            "queryParameters input; got "
            f"{[name for name, _ in populated_parameter_sets]!r}"
        )
    container_name, email_body = populated_parameter_sets[0]
    normalized_email_body = {_norm(str(key)): value for key, value in email_body.items()}
    if set(normalized_email_body) != {"parentfolderid", "limit", "filter"}:
        _fail(
            f"List Emails {container_name} fields do not match the SDD: "
            f"{sorted(normalized_email_body)!r}"
        )
    if normalized_email_body["limit"] != "10":
        _fail(f"List Emails limit must be '10'; got {normalized_email_body['limit']!r}")
    if normalized_email_body["filter"] != "contains(subject,'urgent')":
        _fail(
            "List Emails filter must be contains(subject,'urgent'); got "
            f"{normalized_email_body['filter']!r}"
        )
    parent_folder = normalized_email_body["parentfolderid"]
    if not isinstance(parent_folder, str) or (
        _norm(parent_folder) != "inbox"
        and OUTLOOK_FOLDER_ID_RE.fullmatch(parent_folder) is None
    ):
        _fail(
            "List Emails parentFolderId must be literal 'Inbox' or a resolved "
            f"Outlook folder reference; got {parent_folder!r}"
        )

    # No task input may quietly consume an extra task-output variable. Every
    # cross-task reference must be one of the source contracts asserted above.
    for logical, task in tasks.items():
        for input_name, item in _inputs(task).items():
            refs = set(VAR_REF_RE.findall(str(item.get("value") or "")))
            if refs and (logical, input_name) not in expected_ref_locations:
                _fail(
                    f"unexpected task-output reference(s) {sorted(refs)} in "
                    f"{logical!r} input {input_name!r}"
                )
            dangling = refs - set(outputs_by_id)
            if dangling:
                _fail(
                    f"unproduced variable reference(s) {sorted(dangling)} in "
                    f"{logical!r} input {input_name!r}"
                )

    variables = plan.get("variables") or {}
    nonempty_case_vars = {
        name: variables.get(name)
        for name in ("inputs", "outputs", "inputOutputs")
        if variables.get(name)
    }
    if nonempty_case_vars:
        _fail(f"SDD declares no case variables; found {nonempty_case_vars!r}")

    expected_recipient = _expected_recipient()
    for logical in (
        ("Stage 2", "Manager Approval"),
        ("Stage 4", "Rework Approval"),
    ):
        recipient = (tasks[logical].get("data") or {}).get("recipient")
        if recipient != expected_recipient:
            _fail(
                f"{logical!r} recipient must be {expected_recipient!r}; "
                f"got {recipient!r}"
            )


def _selected_tasks(rule: dict, task_ids: dict) -> tuple[tuple[str, str], ...]:
    ids = list(rule.get("selectedTasksIds") or [])
    if rule.get("selectedTaskId"):
        ids.append(rule["selectedTaskId"])
    logical = []
    for task_id in ids:
        if task_id not in task_ids:
            _fail(f"condition references unknown task id {task_id!r}")
        logical.append(task_ids[task_id])
    return tuple(sorted(logical))


def _selected_stages(rule: dict, stage_ids: dict) -> tuple[str, ...]:
    ids = list(rule.get("selectedStagesIds") or [])
    if rule.get("selectedStageId"):
        ids.append(rule["selectedStageId"])
    logical = []
    for stage_id in ids:
        if stage_id not in stage_ids:
            _fail(f"condition references unknown stage id {stage_id!r}")
        logical.append(stage_ids[stage_id])
    return tuple(sorted(logical))


def _canonical_expression(expression, output_ids: dict):
    if expression in (None, ""):
        return None
    if not isinstance(expression, str):
        return ("invalid", repr(expression))
    match = GATE_RE.fullmatch(expression)
    if match is None:
        return ("raw", re.sub(r"\s+", "", expression))
    output_id, _, value = match.groups()
    producer = output_ids.get(output_id)
    if producer is None:
        _fail(f"gate expression references unproduced variable {output_id!r}")
    return ("equals", producer, value)


def _condition_signature(
    condition: dict, stage_ids: dict, task_ids: dict, output_ids: dict
):
    groups = condition.get("rules") or []
    if len(groups) != 1 or not isinstance(groups[0], list) or len(groups[0]) != 1:
        _fail(
            f"condition {condition.get('displayName')!r} must contain exactly "
            f"one rule; got {groups!r}"
        )
    rule = groups[0][0]
    return (
        rule.get("rule"),
        _selected_stages(rule, stage_ids),
        _selected_tasks(rule, task_ids),
        _canonical_expression(rule.get("conditionExpression"), output_ids),
        condition.get("type"),
        condition.get("marksStageComplete"),
    )


def _sig(
    rule: str,
    *,
    stages=(),
    tasks=(),
    expression=None,
    exit_type=None,
    marks=None,
):
    return (
        rule,
        tuple(sorted(stages)),
        tuple(sorted(tasks)),
        expression,
        exit_type,
        marks,
    )


def _assert_condition_set(where: str, actual_conditions: list, expected, indexes):
    stage_ids, task_ids, output_ids = indexes
    actual = Counter(
        _condition_signature(condition, stage_ids, task_ids, output_ids)
        for condition in actual_conditions
    )
    wanted = Counter(expected)
    if actual != wanted:
        _fail(f"{where} conditions differ\n  actual={actual}\n  expected={wanted}")


def _assert_conditions(stages: dict, tasks: dict, stage_ids: dict, task_ids: dict, output_ids):
    manager = ("Stage 2", "Manager Approval")
    rework = ("Stage 4", "Rework Approval")
    indexes = (stage_ids, task_ids, output_ids)

    expected_stage_entries = {
        "Stage 1": [_sig("case-entered")],
        "Stage 2": [_sig("selected-stage-completed", stages=("Stage 1",))],
        "Stage 3": [_sig("selected-stage-completed", stages=("Stage 2",))],
        "Stage 4": [_sig("selected-stage-exited", stages=("Stage 2",))],
        "Stage 5": [_sig("wait-for-connector")],
        "Stage 6": [_sig("selected-stage-completed", stages=("Stage 3",))],
        "Stage 7": [_sig("user-selected-stage")],
        "Stage 8": [_sig("selected-stage-completed", stages=("Stage 7",))],
    }
    expected_stage_exits = {
        "Stage 1": [_sig("required-tasks-completed", exit_type="exit-only", marks=True)],
        "Stage 2": [
            _sig("required-tasks-completed", exit_type="exit-only", marks=True),
            _sig(
                "selected-tasks-completed",
                tasks=(manager,),
                expression=("equals", (*manager, "Action"), "reject"),
                exit_type="exit-only",
                marks=False,
            ),
        ],
        "Stage 3": [_sig("required-tasks-completed", exit_type="exit-only", marks=True)],
        "Stage 4": [
            _sig(
                "required-tasks-completed",
                expression=("equals", (*rework, "Action"), "reject"),
                exit_type="exit-only",
                marks=True,
            ),
            _sig(
                "selected-tasks-completed",
                tasks=(rework,),
                expression=("equals", (*rework, "Action"), "approve"),
                exit_type="return-to-origin",
                marks=False,
            ),
        ],
        "Stage 5": [_sig("required-tasks-completed", exit_type="wait-for-user", marks=True)],
        "Stage 6": [_sig("required-tasks-completed", exit_type="exit-only", marks=True)],
        "Stage 7": [_sig("required-tasks-completed", exit_type="exit-only", marks=True)],
        "Stage 8": [_sig("required-tasks-completed", exit_type="exit-only", marks=True)],
    }

    for stage_key, stage in stages.items():
        data = stage.get("data") or {}
        _assert_condition_set(
            f"stage {stage_key!r} entry",
            data.get("entryConditions") or [],
            expected_stage_entries[stage_key],
            indexes,
        )
        _assert_condition_set(
            f"stage {stage_key!r} exit",
            data.get("exitConditions") or [],
            expected_stage_exits[stage_key],
            indexes,
        )

    expected_task_entries = {
        ("Stage 1", "Analyze Expense Request"): [_sig("current-stage-entered")],
        ("Stage 1", "Process Expense Request"): [
            _sig(
                "selected-tasks-completed",
                tasks=(("Stage 1", "Analyze Expense Request"),),
            )
        ],
        ("Stage 1", "Record Expense via RPA"): [
            _sig(
                "selected-tasks-completed",
                tasks=(("Stage 1", "Process Expense Request"),),
            )
        ],
        ("Stage 2", "Manager Approval"): [_sig("current-stage-entered")],
        ("Stage 2", "Wait for timer - S2 run once"): [_sig("current-stage-entered")],
        ("Stage 2", "Call Expense API"): [
            _sig("selected-tasks-completed", tasks=(manager,))
        ],
        ("Stage 2", "Wait for timer - S2 adhoc"): [_sig("adhoc")],
        ("Stage 3", "Wait for HTTP Webhook"): [_sig("current-stage-entered")],
        ("Stage 3", "List Emails"): [
            _sig(
                "selected-tasks-completed",
                tasks=(("Stage 3", "Wait for HTTP Webhook"),),
            )
        ],
        ("Stage 3", "Start Child Case"): [
            _sig(
                "selected-tasks-completed",
                tasks=(("Stage 3", "List Emails"),),
            )
        ],
        ("Stage 4", "Rework Approval"): [_sig("current-stage-entered")],
        ("Stage 5", "Wait for timer - S5"): [_sig("current-stage-entered")],
        ("Stage 6", "Timer to be interrupted"): [_sig("current-stage-entered")],
        ("Stage 7", "Wait for timer - S7"): [_sig("current-stage-entered")],
        ("Stage 8", "Wait for timer - S8"): [_sig("runs-sequentially")],
    }
    for logical, task in tasks.items():
        _assert_condition_set(
            f"task {logical!r} entry",
            task.get("entryConditions") or [],
            expected_task_entries[logical],
            indexes,
        )
        _assert_condition_set(
            f"task {logical!r} exit",
            task.get("exitConditions") or [],
            [],
            indexes,
        )


def main():
    plan = _read_plan()
    (
        stages,
        stage_ids,
        tasks,
        task_ids,
        outputs,
        output_ids,
    ) = _index_plan(plan)
    _assert_dataflow(plan, tasks, outputs, output_ids)
    _assert_conditions(stages, tasks, stage_ids, task_ids, output_ids)

    print(
        "OK: CM-Golden caseplan deterministically matches SDD dataflow "
        "sources/completeness, normalized stage/task conditions, and "
        "reject/approve gate polarity"
    )


if __name__ == "__main__":
    main()
