"""check_io_binding_run.py against the plans of two real runs.

testdata/ holds the caseplans of two real builds, one that passed and one that
failed (three task inputs written as `vars.<id>` without the `=`, which the
runtime passes on as text). No io_binding
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
import inspect
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

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


@pytest.fixture
def unbound_consumers_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(grader, "assert_consumers_bound", lambda tasks: None)


def test_the_codex_plan_fails_on_the_literal_its_consumer_binds() -> None:
    with pytest.raises(SystemExit, match="'Consume colliding output' must bind APIInput1 to '=vars.estimatedAge2'"):
        grader.check_plan(FAILING)


@pytest.mark.usefixtures("unbound_consumers_allowed")
def test_the_codex_run_fails_on_the_text_its_input_received() -> None:
    with pytest.raises(SystemExit, match="'Echo prior output' received APIInput1='vars.APIOutput1'"):
        _check(FAILING, *_run(FAILING))


@pytest.mark.usefixtures("unbound_consumers_allowed")
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


# The id the Automation Suite 2.2610 ETE minted for a plan whose identifier is
# IOB (adhoc-2026-11-20_06-39-43), and the one of the next ETE run.
AS_CASE_ID = "17980423"
OTHER_AS_CASE_ID = "57247565"


def test_metadata_equal_to_a_case_id_the_tenant_did_not_prefix_passes() -> None:
    values = {**GLOBALS, "metadataResult": AS_CASE_ID, "CaseId": AS_CASE_ID}
    _check(PASSING, *_run(PASSING, values))


def test_metadata_that_is_another_unprefixed_id_fails() -> None:
    values = {**GLOBALS, "metadataResult": OTHER_AS_CASE_ID, "CaseId": AS_CASE_ID}
    payload, evidence = _run(PASSING, values)
    with pytest.raises(SystemExit, match=f"metadataResult is '{OTHER_AS_CASE_ID}', expected the case's id '{AS_CASE_ID}'"):
        _check(PASSING, payload, evidence)


NO_CASE_ID = {k: v for k, v in GLOBALS.items() if k != "CaseId"}


@pytest.mark.parametrize("case_id", ["IOB-51234", AS_CASE_ID])
def test_metadata_equal_to_the_instances_own_external_id_passes_on_either_id_format(case_id: str) -> None:
    payload, evidence = _run(PASSING, {**NO_CASE_ID, "metadataResult": case_id})

    grader.check_run(payload, evidence, grader.check_plan(PASSING), case_id)


@pytest.mark.parametrize(
    ("metadata", "external_id"),
    [("IOB-1", "IOB-51234"), ("IOB-51234", AS_CASE_ID), (OTHER_AS_CASE_ID, AS_CASE_ID), (None, AS_CASE_ID)],
)
def test_metadata_that_is_not_the_instances_external_id_fails(metadata: object, external_id: str) -> None:
    payload, evidence = _run(PASSING, {**NO_CASE_ID, "metadataResult": metadata})
    with pytest.raises(SystemExit, match=f"metadataResult is .*expected the case's id '{external_id}'"):
        grader.check_run(payload, evidence, grader.check_plan(PASSING), external_id)


@pytest.mark.parametrize("values", [
    {**NO_CASE_ID, "metadataResult": int(AS_CASE_ID)},
    {**GLOBALS, "metadataResult": int(AS_CASE_ID), "CaseId": AS_CASE_ID},
])
def test_metadata_that_is_the_ids_number_and_not_its_string_fails(values: dict) -> None:
    """The SDD declares metadataResult a string; Automation Suite's bare id is the string, not the number."""
    payload, evidence = _run(PASSING, values)
    with pytest.raises(SystemExit, match=f"metadataResult is {AS_CASE_ID}, expected the case's id '{AS_CASE_ID}' as a string"):
        grader.check_run(payload, evidence, grader.check_plan(PASSING), AS_CASE_ID)


def test_the_instances_external_id_outranks_the_case_id_variable() -> None:
    values = {**GLOBALS, "metadataResult": "IOB-51234", "CaseId": "IOB-51234"}
    payload, evidence = _run(PASSING, values)
    with pytest.raises(SystemExit, match=f"expected the case's id '{AS_CASE_ID}'"):
        grader.check_run(payload, evidence, grader.check_plan(PASSING), AS_CASE_ID)


@pytest.mark.parametrize("metadata", ["IOB-51234", AS_CASE_ID, "garbage", None, "=js:metadata.ExternalId"])
def test_a_run_that_names_no_case_id_fails_whatever_metadata_holds(metadata: object) -> None:
    payload, evidence = _run(PASSING, {**NO_CASE_ID, "metadataResult": metadata})
    with pytest.raises(SystemExit, match="the run names no case id .*metadataResult .* cannot be checked"):
        grader.check_run(payload, evidence, grader.check_plan(PASSING), None)


def _stub_instance_get(monkeypatch: pytest.MonkeyPatch, stdout: str, returncode: int = 0) -> list[list[str]]:
    """Answer the CLI call under `_uip`, which the checker reads the instance through."""
    calls: list[list[str]] = []

    class Done:
        stderr = ""

    def run(cmd, *, timeout, what):
        calls.append(list(cmd))
        done = Done()
        done.stdout, done.returncode = stdout, returncode
        return done

    monkeypatch.setattr(sys.modules[grader._uip.__module__], "_run", run)
    return calls


@pytest.mark.parametrize("external_id", ["IOB-53208293", AS_CASE_ID])
def test_the_external_id_is_read_from_the_instance_itself(monkeypatch: pytest.MonkeyPatch, external_id: str) -> None:
    envelope = json.dumps({"Result": "Success", "Data": {"InstanceId": "i-1", "ExternalId": external_id}})
    calls = _stub_instance_get(monkeypatch, envelope)

    assert grader.instance_external_id({"instanceId": "i-1"}, "folder-1") == external_id
    assert calls == [["uip", "maestro", "case", "instance", "get", "i-1", "--folder-key", "folder-1", "--output", "json"]]


@pytest.mark.parametrize(
    "stdout",
    ['{"Result": "Success", "Data": {"InstanceId": "i-1"}}', '{"Result": "Success", "Data": {"ExternalId": ""}}'],
)
def test_an_instance_that_reports_no_external_id_gives_none(monkeypatch: pytest.MonkeyPatch, stdout: str) -> None:
    _stub_instance_get(monkeypatch, stdout)

    assert grader.instance_external_id({"instanceId": "i-1"}, "folder-1") is None


@pytest.mark.parametrize(
    ("stdout", "returncode"),
    [
        ('{"Result": "Failure", "Message": "not found"}', 1),
        ('{"Result": "Failure", "Message": "not found"}', 0),
        ('{"Result": "Success", "Data": {"ExternalId": "IOB-1"}}', 1),
        ("not json", 0),
    ],
)
def test_a_failed_instance_read_fails_the_check(monkeypatch: pytest.MonkeyPatch, stdout: str, returncode: int) -> None:
    """A read that failed is not an instance without an id: it must not fall through to the CaseId variable."""
    _stub_instance_get(monkeypatch, stdout, returncode)
    with pytest.raises(SystemExit, match="uip maestro case instance get failed"):
        grader.instance_external_id({"instanceId": "i-1"}, "folder-1")


def test_a_payload_with_no_instance_id_gives_no_external_id() -> None:
    assert grader.instance_external_id({}, "folder-1") is None


def test_the_run_is_read_with_one_folder_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """The instance get reuses the folder key read_run resolved: the instance list is scanned once."""
    evidence_module = sys.modules[grader._uip.__module__]
    lookups: list[str] = []
    monkeypatch.setattr(evidence_module, "folder_key_of", lambda instance_id, since: lookups.append(instance_id) or "folder-1")
    calls = _stub_instance_get(monkeypatch, json.dumps({"Result": "Success", "Data": {"ExternalId": AS_CASE_ID}}))
    payload = {"instanceId": "i-1"}

    evidence = grader.read_run(payload, "2026-11-23T00:00:00Z")

    assert grader.instance_external_id(payload, evidence.folder_key) == AS_CASE_ID
    assert lookups == ["i-1"]
    assert [call[4] for call in calls] == ["variables-all", "get"]
    assert all(call[call.index("--folder-key") + 1] == "folder-1" for call in calls)


TASK_YAML = HERE / "io_binding.yaml"
RUN_CRITERION_COMMAND = "check_io_binding_run.py"


def test_the_run_criterion_timeout_covers_the_worst_case_grader_run() -> None:
    task = yaml.safe_load(TASK_YAML.read_text(encoding="utf-8"))
    criterion = next(c for c in task["success_criteria"] if RUN_CRITERION_COMMAND in c.get("command", ""))
    case_check = sys.modules[grader.run_debug.__module__]
    evidence_module = sys.modules[grader._uip.__module__]
    refresh_s = inspect.signature(case_check.run_debug).parameters["refresh_timeout"].default
    starts = 2  # run_debug starts the case again after a Cancelled run
    calls_per_start = 2  # each start retries one transient fault
    worst_case_s = (
        starts * (refresh_s + calls_per_start * grader.DEBUG_TIMEOUT_S)
        + (starts * (calls_per_start - 1) + starts - 1) * case_check._DEBUG_RETRY_SLEEP_S
        + evidence_module.LIST_DEADLINE_S  # the one folder lookup
        + 2 * evidence_module.READ_TIMEOUT_S  # variables-all, then instance get
    )

    assert criterion["timeout"] >= worst_case_s


def test_the_task_timeout_outlasts_the_turn_and_every_criterion() -> None:
    task = yaml.safe_load(TASK_YAML.read_text(encoding="utf-8"))
    limits = task["run_limits"]
    criteria = sum(c.get("timeout", 0) for c in task["success_criteria"])

    assert limits["task_timeout"] > limits["turn_timeout"] + criteria


@pytest.mark.parametrize("identifier", ["IoBindingCase", "iob", "", None])
def test_a_plan_without_the_sdds_identifier_prefix_fails(identifier: object) -> None:
    plan = copy.deepcopy(PASSING)
    plan["metadata"]["caseIdentifier"] = identifier
    with pytest.raises(SystemExit, match="the plan's case identifier is .* the SDD names the prefix 'IOB'"):
        grader.check_plan(plan)


@pytest.mark.parametrize("kind", ["external", "", None])
def test_a_plan_whose_identifier_is_not_a_constant_prefix_fails(kind: object) -> None:
    plan = copy.deepcopy(PASSING)
    plan["metadata"]["caseIdentifierType"] = kind
    with pytest.raises(SystemExit, match=r"case identifier is 'IOB' \(type .*\), the SDD names the prefix 'IOB' \(type 'constant'\)"):
        grader.check_plan(plan)


def test_a_plan_with_no_metadata_fails_on_the_identifier() -> None:
    plan = copy.deepcopy(PASSING)
    del plan["metadata"]
    with pytest.raises(SystemExit, match="the plan's case identifier is None"):
        grader.check_plan(plan)


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
    """Any unique collision id, binding layout and output-row shape passes."""
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


def _with_lookup_output(evidence: object, age: object) -> object:
    """The colliding lookup returned ``age`` in its own outputs."""
    lookup = next(t for t in _tasks(PASSING) if t["displayName"] == "Lookup colliding same name")
    for element in evidence.elements[lookup["id"]]:
        element["Outputs"] = {"EstimatedAge": age}
    return evidence


def test_a_null_input_on_consume_colliding_output_fails_when_the_lookup_returned_an_age(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(STATE, "estimatedAge2", None)
    values = {**GLOBALS, "estimatedAge": 31, "collisionCopy": 31, "customReferenceCopy": 31}
    monkeypatch.setitem(STATE, "collisionCopy", 31)
    payload, evidence = _run(PASSING, values)
    with pytest.raises(SystemExit, match="'Consume colliding output' ran without"):
        _check(PASSING, payload, _with_lookup_output(evidence, 31))


def test_a_null_input_on_consume_custom_output_fails_when_collision_copy_has_a_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(STATE, "collisionCopy", None)
    with pytest.raises(SystemExit, match="'Consume custom output' ran without"):
        _check(PASSING, *_run(PASSING))


def test_both_copies_null_fail_when_the_lookup_returned_an_age(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(STATE, "estimatedAge2", 31)
    monkeypatch.setitem(STATE, "collisionCopy", 31)
    values = {**GLOBALS, "estimatedAge": 31, "collisionCopy": None, "customReferenceCopy": None}
    payload, evidence = _run(PASSING, values)
    with pytest.raises(SystemExit, match="customReferenceCopy"):
        _check(PASSING, payload, _with_lookup_output(evidence, 31))


@pytest.mark.parametrize(
    ("consumer", "expected"),
    [("Consume colliding output", "=vars.estimatedAge2"), ("Consume custom output", "=vars.collisionCopy")],
)
@pytest.mark.parametrize("bound", [None, "", "literal-seed", "=vars.estimatedAge", "vars.estimatedAge2"])
def test_an_agify_fed_input_not_bound_to_its_producer_fails(consumer: str, expected: str, bound: object) -> None:
    plan = copy.deepcopy(PASSING)
    task = next(t for t in _tasks(plan) if t["displayName"] == consumer)
    task["data"]["inputs"][0]["value"] = bound
    with pytest.raises(SystemExit, match=f"'{consumer}' must bind APIInput1 to '{expected}'"):
        grader.check_plan(plan)


def test_an_agify_fed_task_without_the_input_row_fails() -> None:
    plan = copy.deepcopy(PASSING)
    task = next(t for t in _tasks(plan) if t["displayName"] == "Consume custom output")
    task["data"]["inputs"] = []
    with pytest.raises(SystemExit, match="'Consume custom output' must bind APIInput1"):
        grader.check_plan(plan)
