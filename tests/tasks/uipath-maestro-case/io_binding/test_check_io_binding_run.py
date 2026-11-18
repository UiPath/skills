"""check_io_binding_run.py against the plans of two real runs.

testdata/ holds the caseplan of nightly 2026-11-18_04-23-44 (claude-code, passed)
and of 2026-11-17_04-23-38 (codex, failed: three task inputs written as
`vars.<id>` without the `=`, which the runtime passes on as text). No io_binding
debug run left instance evidence, so `_run()` builds it in the shape a real run
returns (single_node/http_request/testdata and single_node/business_rule/testdata:
PascalCased `Globals` / `GlobalDefinitions`, task inputs under `JobArguments`),
resolving each plan input the way the runtime does: `=vars.<id>` reads the
variable, the one `=js:` concatenation here is evaluated, anything else is text.
No tenant is touched.

    cd tests && uv run -q --with pytest python -m pytest -q tasks/uipath-maestro-case/io_binding
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PASSING = json.loads((HERE / "testdata" / "plan_claude_2026-11-18_pass.json").read_text())
FAILING = json.loads((HERE / "testdata" / "plan_codex_2026-11-17_fail.json").read_text())


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


grader = _load("check_io_binding_run_under_test", HERE / "check_io_binding_run.py")

# What the echo API and agify give back for the SDD's inputs.
STATE = {
    "caseInput": "case-seed",
    "APIOutput1": "literal-seed",
    "renamedResult": "case-seed",
    "estimatedAge": None,
    "estimatedAge2": None,
    "collisionCopy": 0,
}
GLOBALS = {
    "caseInput": "case-seed",
    "renamedResult": "case-seed",
    "errorMessage": None,
    "literalResult": "literal-assigned",
    "copiedResult": "case-seed",
    "computedResult": "literal-seed-computed",
    "metadataResult": "IOB-51234",
    "estimatedAge": None,
    "collisionCopy": 0,
    "customReferenceCopy": 0,
    "CaseId": "IOB-51234",
}


def _resolve(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value.startswith("=vars."):
        return STATE.get(value[len("=vars."):])
    concat = re.fullmatch(r"=js:vars\.(\w+) \+ '([^']*)'", value)
    if concat:
        return f"{STATE.get(concat.group(1))}{concat.group(2)}"
    return value


def _tasks(plan: dict) -> list[dict]:
    return [t for n in plan["nodes"] for lane in n["data"].get("tasks") or [] for t in lane]


def _run(plan: dict, globals_: dict | None = None) -> tuple[dict, object]:
    executions, elements = [], []
    for minute, task in enumerate(_tasks(plan)):
        executions.append({
            "elementId": task["id"], "elementType": "ServiceTask", "status": "Completed",
            "startedAt": f"2026-11-18T05:{10 + minute:02d}:00.1234567Z",
            "completedAt": f"2026-11-18T05:{10 + minute:02d}:30.98Z",
        })
        arguments = {i["name"][0].upper() + i["name"][1:]: _resolve(i.get("value"))
                     for i in task["data"]["inputs"]}
        elements.append({"ElementId": task["id"], "Inputs": {"JobArguments": arguments}, "Outputs": {}})
    values = GLOBALS if globals_ is None else globals_
    variables_all = {"Variables": [
        {
            "ParentElementId": None,
            "Globals": {k[0].upper() + k[1:]: v for k, v in values.items()},
            "GlobalDefinitions": {k[0].upper() + k[1:]: {"Name": k, "Type": "string"} for k in values},
            "Elements": [],
        },
        {"ParentElementId": "tasksEventSubProcess", "Globals": {}, "Elements": elements},
    ]}
    payload = {"instanceId": "i-1", "finalStatus": "Completed", "elementExecutions": executions}
    return payload, grader.RunEvidence(variables_all)


def _check(plan: dict, payload: dict, evidence: object) -> None:
    grader.check_run(payload, evidence, grader.check_plan(plan))


def test_the_passing_run_passes() -> None:
    _check(PASSING, *_run(PASSING))


def test_the_codex_plan_passes_the_static_checks() -> None:
    """Its defect is invisible to the plan's shape; the run is what shows it."""
    assert [t["displayName"] for t in grader.check_plan(FAILING)][2] == "Echo prior output"


def test_the_codex_run_fails_on_the_text_its_input_received() -> None:
    with pytest.raises(SystemExit, match="'Echo prior output' received APIInput1='vars.APIOutput1'"):
        _check(FAILING, *_run(FAILING))


def test_an_unresolved_reference_on_an_agify_fed_task_fails() -> None:
    plan = copy.deepcopy(PASSING)
    consumer = next(t for t in _tasks(plan) if t["displayName"] == "Consume custom output")
    consumer["data"]["inputs"][0]["value"] = "vars.collisionCopy"
    with pytest.raises(SystemExit, match="instead of the value it refers to"):
        _check(plan, *_run(plan))


@pytest.mark.parametrize(
    ("name", "wrong"),
    [("copiedResult", "=vars.renamedResult"), ("computedResult", "-computed"),
     ("literalResult", '"literal-assigned"'), ("renamedResult", None)],
)
def test_a_wrong_named_output_fails(name: str, wrong: object) -> None:
    payload, evidence = _run(PASSING, {**GLOBALS, name: wrong})
    with pytest.raises(SystemExit, match=name):
        _check(PASSING, payload, evidence)


def test_metadata_must_be_the_cases_own_id() -> None:
    payload, evidence = _run(PASSING, {**GLOBALS, "metadataResult": "IOB-1"})
    with pytest.raises(SystemExit, match="metadataResult"):
        _check(PASSING, payload, evidence)


def test_custom_reference_copy_must_follow_collision_copy() -> None:
    payload, evidence = _run(PASSING, {**GLOBALS, "customReferenceCopy": 7})
    with pytest.raises(SystemExit, match="customReferenceCopy"):
        _check(PASSING, payload, evidence)


def test_nan_from_a_null_age_counts_as_the_same_value() -> None:
    nan = float("nan")
    _check(PASSING, *_run(PASSING, {**GLOBALS, "collisionCopy": nan, "customReferenceCopy": nan}))


def test_tasks_out_of_order_fail() -> None:
    payload, evidence = _run(PASSING)
    executions = payload["elementExecutions"]
    executions[3]["startedAt"] = executions[2]["startedAt"]
    with pytest.raises(SystemExit, match="'Echo expression' started before 'Echo prior output'"):
        _check(PASSING, payload, evidence)


def test_a_failed_task_fails() -> None:
    payload, evidence = _run(PASSING)
    payload["elementExecutions"][5]["status"] = "Faulted"
    with pytest.raises(SystemExit, match="'Lookup colliding same name' finished 'Faulted'"):
        _check(PASSING, payload, evidence)


def test_another_collision_id_and_binding_layout_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    """The old grader pinned `estimatedAge2`, four deduplicated bindings and the
    exact output-row shapes; any unique ids and any binding layout pass now."""
    plan = copy.deepcopy(PASSING)
    tasks = _tasks(plan)
    colliding = next(t for t in tasks if t["displayName"] == "Lookup colliding same name")
    colliding["data"]["outputs"][0]["id"] = "estimatedAge_2"
    consumer = next(t for t in tasks if t["displayName"] == "Consume colliding output")
    consumer["data"]["inputs"][0]["value"] = "=vars.estimatedAge_2"
    for index, task in enumerate(tasks):
        for prop in ("name", "folderPath"):
            old = task["data"][prop][len("=bindings."):]
            binding = copy.deepcopy(next(b for b in plan["bindings"] if b["id"] == old))
            binding["id"] = f"b{prop}{index}"
            plan["bindings"].append(binding)
            task["data"][prop] = f"=bindings.{binding['id']}"
    monkeypatch.setitem(STATE, "estimatedAge_2", None)
    _check(plan, *_run(plan))


def test_a_task_bound_to_another_folder_fails() -> None:
    plan = copy.deepcopy(PASSING)
    for binding in plan["bindings"]:
        binding["resourceKey"] = str(binding["resourceKey"]).replace("NameToAgeFixed2", "NameToAgeFixed")
        if binding.get("default") == "Shared/uipath-maestro-case/NameToAgeFixed2":
            binding["default"] = "Shared/uipath-maestro-case/NameToAgeFixed"
    with pytest.raises(SystemExit, match="NameToAgeFixed2"):
        grader.check_plan(plan)


def test_a_missing_sdd_task_fails() -> None:
    plan = copy.deepcopy(PASSING)
    for node in plan["nodes"]:
        tasks = node["data"].get("tasks")
        if tasks:
            node["data"]["tasks"] = [[t for t in lane if t["displayName"] != "Echo expression"] for lane in tasks]
    with pytest.raises(SystemExit, match="expected the SDD's 8 api-workflow tasks, got 7"):
        grader.check_plan(plan)
