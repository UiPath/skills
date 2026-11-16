"""Offline self-tests for check_trigger_run.py, the Test Manager event-trigger grader.

The 33 tasks stay `skip: true` until the uip CLI stops uppercasing Test Manager's
mixed-case trigger operations, so the grader cannot run end to end yet. These
tests pin its logic instead: small fixture artifacts in a temp dir for
`--artifact`, and a fake `run_uip` that answers from canned records and jobs for
`--live`. No tenant, no credentials, no real `uip`.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CONNECTOR = "uipath-uipath-testmanager"
MARKER = "DataEval-0123abcd"
PROJECT = "11111111-1111-1111-1111-111111111111"
RECORD = "22222222-2222-2222-2222-222222222222"
EXECUTION = "33333333-3333-3333-3333-333333333333"
COPY = "44444444-4444-4444-4444-444444444444"
CONNECTION = "55555555-5555-5555-5555-555555555555"


@pytest.fixture
def grader(monkeypatch):
    """A fresh copy of the grader per test, so monkeypatched constants never leak."""
    spec = importlib.util.spec_from_file_location("check_trigger_run_under_test", HERE / "check_trigger_run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def no_real_uip(*args, **kwargs):
        raise AssertionError(f"unexpected uip call: {args}")

    monkeypatch.setattr(module, "run_uip", no_real_uip)
    monkeypatch.setattr(module, "LIVE_WAIT", 0)  # one poll pass
    monkeypatch.setattr(module.time, "sleep", lambda s: None)
    return module


def seed_for(operation, object_type, **extra):
    seed = {
        "marker": MARKER,
        "operation": operation,
        "object_type": object_type,
        "process_name": f"TmTrigger_{MARKER}",
        "deployment_name": f"TmTrigger_{MARKER}",
        "started_at": "2026-11-16T00:00:00Z",
    }
    if operation == "Updated":
        seed["updated_description"] = f"updated by {MARKER}"
    if object_type in ("TestExecution", "TestCaseLog"):
        seed["execution_test_set_id"] = COPY
        seed["execution_test_set"] = "HEALTH:99"
    seed.update(extra)
    return seed


def expect_fail(capsys, fn, *args):
    with pytest.raises(SystemExit) as exc:
        fn(*args)
    assert exc.value.code == 1
    return capsys.readouterr().out


def expect_ok(capsys, fn, *args):
    fn(*args)
    out = capsys.readouterr().out
    assert out.startswith("OK:"), out
    return out


def run_main(grader, monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["check_trigger_run.py", *argv])
    grader.main()


# ================================================================ has_token


@pytest.mark.parametrize(
    "text, word, expected",
    [
        ("TestCase", "TestCase", True),
        ("testcase", "TestCase", True),
        ("TestCaseLog", "TestCase", False),
        ('"object": "testcaselog"', "TestCase", False),
        ("Updated", "Updated", True),
        ("updatedAt", "Updated", False),
        ('"field": "updatedat"', "Updated", False),
        ("RECORD_CREATED", "Created", True),
        ("Record Updated", "Updated", True),
        ("record-finished", "Finished", True),
        ("Created2", "Created", False),
        ("ReCreated", "Created", False),
    ],
)
def test_has_token_matches_whole_tokens_only(grader, text, word, expected):
    assert grader.has_token(text, word) is expected


# ================================================================ --artifact api-workflow


def write_api_workflow(root: Path, *, operation="Created", obj="TestCase", extra=None,
                       bindings=True, binding_ops=("Created",), placeholder=False):
    project = root / "TmTriggerApi"
    project.mkdir(parents=True, exist_ok=True)
    trigger = {
        "call": "UiPath.IntSvcEvent",
        "with": {
            "connectorKey": CONNECTOR,
            "objectName": "TestManagerEvents",
            "operation": operation,
            "eventParameters": {"objectType": obj},
            "connectionId": "<REPLACE_WITH_CONNECTION_ID>" if placeholder else CONNECTION,
            **(extra or {}),
        },
    }
    workflow = {
        "document": {"name": "TmTriggerApi"},
        "do": [{"Sequence_1": {"do": [
            {"WorkflowStart": {"set": {}}},
            {"Record_Trigger": trigger},
            {"Return": {"set": {"payload": "${$context.trigger}"}}},
        ]}}],
    }
    (project / "Workflow.json").write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    if bindings:
        resources = [{"resource": "Connection", "key": CONNECTION}]
        resources += [{"resource": "EventTrigger", "metadata": {"Operation": op}} for op in binding_ops]
        (project / "bindings_v2.json").write_text(json.dumps({"version": "2.0", "resources": resources}), encoding="utf-8")
    return project


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def write_seed(sandbox: Path, seed):
    (sandbox / "seed.json").write_text(json.dumps(seed), encoding="utf-8")


def test_api_workflow_correct_trigger_passes_via_main(grader, sandbox, monkeypatch, capsys):
    write_seed(sandbox, seed_for("Created", "TestCase"))
    write_api_workflow(sandbox)
    run_main(grader, monkeypatch, "--artifact", "api-workflow")
    assert "starts on Test Manager Record Created / TestCase, EventTrigger bound" in capsys.readouterr().out


def test_api_workflow_uppercased_operation_still_matches(grader, sandbox, capsys):
    write_api_workflow(sandbox, operation="RECORD_CREATED", binding_ops=("RECORD_CREATED",))
    expect_ok(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))


def test_api_workflow_testcaselog_does_not_match_testcase(grader, sandbox, capsys):
    write_api_workflow(sandbox, obj="TestCaseLog")
    out = expect_fail(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))
    assert "no Workflow.json whose first activity" in out


def test_api_workflow_updatedat_field_does_not_match_updated(grader, sandbox, capsys):
    # Created trigger whose output mapping mentions updatedAt must not pass as Record Updated.
    write_api_workflow(sandbox, operation="Created", extra={"select": ["id", "updatedAt"]})
    out = expect_fail(capsys, grader.check_api_workflow, seed_for("Updated", "TestCase"))
    assert "Record Updated trigger" in out


def test_api_workflow_trigger_not_first_after_start_fails(grader, sandbox, capsys):
    project = write_api_workflow(sandbox)
    doc = json.loads((project / "Workflow.json").read_text(encoding="utf-8"))
    steps = doc["do"][0]["Sequence_1"]["do"]
    steps.insert(1, {"Log": {"call": "UiPath.Log", "with": {"message": "hi"}}})
    (project / "Workflow.json").write_text(json.dumps(doc), encoding="utf-8")
    expect_fail(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))


def test_api_workflow_missing_bindings_fails(grader, sandbox, capsys):
    write_api_workflow(sandbox, bindings=False)
    out = expect_fail(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))
    assert "bindings_v2.json missing" in out


def test_api_workflow_binding_with_wrong_operation_fails(grader, sandbox, capsys):
    write_api_workflow(sandbox, binding_ops=("Updated",))
    out = expect_fail(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))
    assert "is not Record Created" in out


def test_api_workflow_two_event_triggers_fail(grader, sandbox, capsys):
    write_api_workflow(sandbox, binding_ops=("Created", "Created"))
    out = expect_fail(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))
    assert "2 EventTrigger entries" in out


def test_api_workflow_unresolved_placeholder_fails(grader, sandbox, capsys):
    write_api_workflow(sandbox, placeholder=True)
    out = expect_fail(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))
    assert "REPLACE_WITH" in out


def test_api_workflow_none_found_fails(grader, sandbox, capsys):
    out = expect_fail(capsys, grader.check_api_workflow, seed_for("Created", "TestCase"))
    assert "no Workflow.json inside a project folder" in out


# ================================================================ --artifact rpa

XAML = """<Activity x:Class="Main"
  xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
  xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
  xmlns:uix="http://schemas.uipath.com/workflow/integration-service-activities/uix">
  <Sequence DisplayName="Main Sequence">
    <Sequence.Variables>
      <Variable x:TypeArguments="x:String" Name="TestCase_Created_Updated" />
    </Sequence.Variables>
    {first}
    <WriteLine Text="done" />
  </Sequence>
</Activity>
"""

TRIGGER = """<uix:ConnectorTriggerActivity DisplayName="Test Manager trigger"
      ConnectorKey="uipath-uipath-testmanager" ObjectName="{obj}" Operation="{op}"
      ConnectionId="{conn}">
      <uix:ConnectorTriggerActivity.OutputSchema>
        <uix:Field Name="updatedAt" />
        <uix:Field Name="testCaseLogId" />
        <uix:Field Name="Record Updated" />
      </uix:ConnectorTriggerActivity.OutputSchema>
    </uix:ConnectorTriggerActivity>"""


def write_rpa(root: Path, *, op="Created", obj="TestCase", conn=CONNECTION, first=None):
    project = root / "TmTriggerRpa"
    project.mkdir(parents=True, exist_ok=True)
    first = first if first is not None else TRIGGER.format(op=op, obj=obj, conn=conn)
    (project / "Main.xaml").write_text(XAML.replace("{first}", first), encoding="utf-8")


def test_rpa_correct_trigger_passes_via_main(grader, sandbox, monkeypatch, capsys):
    write_seed(sandbox, seed_for("Created", "TestCase"))
    write_rpa(sandbox)
    run_main(grader, monkeypatch, "--artifact", "rpa")
    assert "starts on the Test Manager Record Created trigger for TestCase" in capsys.readouterr().out


def test_rpa_reads_only_the_trigger_attributes_not_its_child_schema(grader, sandbox, capsys):
    # The child output schema says updatedAt / Record Updated / testCaseLogId, but the
    # trigger itself is Record Created on TestCase: it is not an Updated or TestCaseLog trigger.
    write_rpa(sandbox)
    expect_fail(capsys, grader.check_rpa, seed_for("Updated", "TestCase"))
    expect_fail(capsys, grader.check_rpa, seed_for("Created", "TestCaseLog"))


def test_rpa_testcaselog_trigger_does_not_match_testcase(grader, sandbox, capsys):
    write_rpa(sandbox, op="Updated", obj="TestCaseLog")
    expect_fail(capsys, grader.check_rpa, seed_for("Updated", "TestCase"))
    expect_ok(capsys, grader.check_rpa, seed_for("Updated", "TestCaseLog"))


@pytest.mark.parametrize("conn", ["", "not-a-guid", "00000000-0000-0000-0000-000000000000", "{{ConnectionId}}"])
def test_rpa_bad_connection_id_fails(grader, sandbox, capsys, conn):
    write_rpa(sandbox, conn=conn)
    out = expect_fail(capsys, grader.check_rpa, seed_for("Created", "TestCase"))
    assert "is not a real connection GUID" in out


def test_rpa_trigger_not_first_activity_fails(grader, sandbox, capsys):
    write_rpa(sandbox, first='<WriteLine Text="first" />\n' + TRIGGER.format(op="Created", obj="TestCase", conn=CONNECTION))
    expect_fail(capsys, grader.check_rpa, seed_for("Created", "TestCase"))


def test_rpa_malformed_xaml_fails(grader, sandbox, capsys):
    (sandbox / "P").mkdir()
    (sandbox / "P" / "Main.xaml").write_text("<Activity><Sequence>", encoding="utf-8")
    out = expect_fail(capsys, grader.check_rpa, seed_for("Created", "TestCase"))
    assert "not well-formed" in out


# ================================================================ --artifact bpmn

BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:uipath="http://uipath.org/schema/bpmn" id="Defs">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="Start_1">
      <bpmn:extensionElements>
        <uipath:entryPointId value="ep-1" />
        <uipath:type value="{type}" />
        <uipath:context>
          <uipath:input name="connectorKey" value="{connector}" />
          <uipath:input name="operation" value="{op}" />
          <uipath:input name="objectName">{obj}</uipath:input>
        </uipath:context>
      </bpmn:extensionElements>
    </bpmn:startEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def write_bpmn(root: Path, *, op="Finished", obj="TestExecution", connector=CONNECTOR, type_="Intsvc.EventTrigger"):
    project = root / "TmTriggerBpmn"
    project.mkdir(parents=True, exist_ok=True)
    (project / "Process.bpmn").write_text(
        BPMN.format(op=op, obj=obj, connector=connector, type=type_), encoding="utf-8")


def test_bpmn_correct_trigger_passes_via_main(grader, sandbox, monkeypatch, capsys):
    write_seed(sandbox, seed_for("Finished", "TestExecution"))
    write_bpmn(sandbox)
    run_main(grader, monkeypatch, "--artifact", "bpmn")
    assert "Intsvc.EventTrigger for Test Manager Record Finished / TestExecution" in capsys.readouterr().out


def test_bpmn_uppercased_operation_still_matches(grader, sandbox, capsys):
    write_bpmn(sandbox, op="RECORD_FINISHED")
    expect_ok(capsys, grader.check_bpmn, seed_for("Finished", "TestExecution"))


@pytest.mark.parametrize(
    "kwargs, seed",
    [
        ({"obj": "TestCaseLog"}, ("Finished", "TestCase")),
        ({"op": "Created", "obj": "TestCase"}, ("Updated", "TestCase")),
        ({"connector": "uipath-atlassian-jira"}, ("Finished", "TestExecution")),
        ({"type_": "Intsvc.Activity"}, ("Finished", "TestExecution")),
    ],
    ids=["testcaselog-vs-testcase", "created-vs-updated", "other-connector", "not-an-event-trigger"],
)
def test_bpmn_mismatches_fail(grader, sandbox, capsys, kwargs, seed):
    write_bpmn(sandbox, **kwargs)
    out = expect_fail(capsys, grader.check_bpmn, seed_for(*seed))
    assert "no bpmn:startEvent carrying Intsvc.EventTrigger" in out


# ================================================================ key_field_error


@pytest.mark.parametrize(
    "op, obj, payload, error",
    [
        # Named records: name must be the marker; Updated also needs the new description.
        ("Created", "Requirement", {"name": MARKER}, None),
        ("Created", "TestCase", {"Name": MARKER}, None),
        ("Created", "TestSet", {"name": "someone else"}, "!= seeded marker"),
        ("Updated", "TestCase", {"name": MARKER, "description": f"x updated by {MARKER} y"}, None),
        ("Updated", "Requirement", {"name": MARKER, "description": "stale"}, "does not carry the update"),
        ("Updated", "TestSet", {"name": MARKER}, "does not carry the update"),
        # TestExecution: testSetId always; status past initial for Updated; terminal + executionFinished for Finished.
        ("Created", "TestExecution", {"testSetId": COPY, "status": "Pending"}, None),
        ("Created", "TestExecution", {"status": "Pending"}, "no testSetId"),
        ("Updated", "TestExecution", {"testSetId": COPY, "status": "Running"}, None),
        ("Updated", "TestExecution", {"testSetId": COPY, "status": "NotStarted"}, "has not moved past"),
        ("Updated", "TestExecution", {"testSetId": COPY}, "has not moved past"),
        ("Finished", "TestExecution", {"testSetId": COPY, "status": "Passed", "executionFinished": "2026-11-16T01:00:00Z"}, None),
        ("Finished", "TestExecution", {"testSetId": COPY, "status": "Running", "executionFinished": "x"}, "is not terminal"),
        ("Finished", "TestExecution", {"testSetId": COPY, "status": "Failed"}, "no executionFinished"),
        # TestCaseLog: testCaseId always; result for Finished.
        ("Updated", "TestCaseLog", {"testCaseId": RECORD}, None),
        ("Updated", "TestCaseLog", {"result": "Passed"}, "no testCaseId"),
        ("Finished", "TestCaseLog", {"testCaseId": RECORD, "result": "Passed"}, None),
        ("Finished", "TestCaseLog", {"testCaseId": RECORD}, "has no result"),
    ],
)
def test_key_field_error(grader, op, obj, payload, error):
    got = grader.key_field_error(payload, seed_for(op, obj))
    if error is None:
        assert got is None
    else:
        assert got is not None and error in got, got


# ================================================================ --live


class FakeUip:
    """Answers the grader's uip calls from canned records and jobs, and logs every call."""

    def __init__(self, records=None, jobs=None, job_details=None):
        self.records = records or {}       # (object, id) -> record
        self.jobs = jobs or []
        self.job_details = job_details or {}  # key -> full job
        self.calls = []

    def __call__(self, *args, timeout=60):
        self.calls.append(args)
        if args[:4] == ("is", "resources", "run", "get"):
            assert args[4] == CONNECTOR
            obj = args[5]
            query = dict(part.split("=", 1) for part in args[args.index("--query") + 1].split("&"))
            return self.records.get((obj, query["id"]), {})
        if args[:3] == ("or", "jobs", "list"):
            offset = int(args[args.index("--offset") + 1])
            limit = int(args[args.index("--limit") + 1])
            return {"items": self.jobs[offset:offset + limit]}
        if args[:3] == ("or", "jobs", "get"):
            return self.job_details[args[3]]
        raise AssertionError(f"unexpected uip call: {args}")

    def offsets(self):
        return [int(a[a.index("--offset") + 1]) for a in self.calls if a[:3] == ("or", "jobs", "list")]


def job(key, payload, *, state="Successful", source_type="Trigger", encode=True):
    outputs = {"payload": payload}
    return {"Key": key, "State": state, "SourceType": source_type,
            "OutputArguments": json.dumps(outputs) if encode else outputs}


def named_payload(**extra):
    return {"objectType": "TestCase", "projectId": PROJECT, "id": RECORD, "name": MARKER, **extra}


def write_result(sandbox: Path, **extra):
    result = {"connection_id": CONNECTION, "project_id": PROJECT, "record_id": RECORD,
              "created": [{"object": "TestCase", "id": RECORD}], **extra}
    (sandbox / "result.json").write_text(json.dumps(result), encoding="utf-8")


def install(grader, monkeypatch, fake):
    monkeypatch.setattr(grader, "run_uip", fake)
    return fake


NAMED_RECORDS = {("TestCase", RECORD): {"id": RECORD, "name": MARKER}}


def test_live_passes_on_first_matching_job_after_a_mismatch(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[
        job("job-unrelated", {"objectType": "TestCase", "projectId": PROJECT, "id": "other-record", "name": "x"}),
        job("job-faulted", named_payload(), state="Faulted"),
        job("job-wrong-project", named_payload(projectId="99999999-9999-9999-9999-999999999999")),
        job("job-good", named_payload()),
        job("job-later", named_payload()),
    ]))
    out = expect_ok(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "job job-good was started by the Record Created trigger" in out


def test_live_reports_every_mismatch_when_no_job_holds(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[
        job("job-faulted", named_payload(), state="Faulted"),
        job("job-wrong-type", named_payload(objectType="TestCaseLog")),
    ]))
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "ended 'Faulted'" in out and "payload objectType 'TestCaseLog'" in out


@pytest.mark.parametrize("source_type", ["Manual", "manual", "Studio Web", "RobotAPI", "Assistant"])
def test_live_rejects_manually_started_job(grader, sandbox, monkeypatch, capsys, source_type):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[job("job-1", named_payload(), source_type=source_type)]))
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "was started by hand" in out


def test_live_pages_jobs_list_with_offset(grader, sandbox, monkeypatch, capsys):
    monkeypatch.setattr(grader, "JOB_PAGE", 2)
    write_result(sandbox)
    filler = {"objectType": "TestCase", "projectId": PROJECT, "id": "other", "name": "x"}
    fake = install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[
        job("j1", filler), job("j2", filler), job("j3", filler), job("j4", filler), job("j5", named_payload()),
    ]))
    out = expect_ok(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "job j5" in out
    assert fake.offsets() == [0, 2, 4]
    first = next(a for a in fake.calls if a[:3] == ("or", "jobs", "list"))
    assert first[first.index("--process-name") + 1] == f"TmTrigger_{MARKER}"
    assert first[first.index("--limit") + 1] == "2"


def test_live_paging_stops_on_full_last_page(grader, sandbox, monkeypatch, capsys):
    # Exactly two full pages: the grader must ask once more, get an empty page and stop.
    monkeypatch.setattr(grader, "JOB_PAGE", 2)
    write_result(sandbox)
    filler = {"objectType": "TestCase", "projectId": PROJECT, "id": "other", "name": "x"}
    fake = install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[
        job("j1", filler), job("j2", filler), job("j3", filler), job("j4", named_payload()),
    ]))
    expect_ok(capsys, grader.live, seed_for("Created", "TestCase"))
    assert fake.offsets() == [0, 2, 4]


def test_live_fetches_outputs_when_list_omits_them(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    listed = {"Key": "job-1", "State": "Successful", "SourceType": "Trigger"}
    fake = install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[listed],
                                                job_details={"job-1": job("job-1", named_payload())}))
    expect_ok(capsys, grader.live, seed_for("Created", "TestCase"))
    assert ("or", "jobs", "get", "job-1", "--all-fields", "--no-download") in fake.calls


def test_live_named_record_without_marker_is_not_ours(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip({("TestCase", RECORD): {"id": RECORD, "name": "someone else"}},
                                         jobs=[job("job-1", named_payload())]))
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "not this run's record" in out


def test_live_no_jobs_means_trigger_never_fired(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[]))
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "the trigger never fired" in out


def test_live_jobs_without_our_payload_fail(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(NAMED_RECORDS, jobs=[job("job-1", {"id": "other"})]))
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "1 job(s) ran but none returned a payload" in out


@pytest.mark.parametrize("missing", ["connection_id", "project_id", "record_id"])
def test_live_result_json_needs_ids(grader, sandbox, monkeypatch, capsys, missing):
    write_result(sandbox, **{missing: ""})
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestCase"))
    assert f"result.json has no {missing}" in out


def test_live_missing_result_json_fails(grader, sandbox, capsys):
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestCase"))
    assert "result.json missing" in out


# ---------------------------------------------------------------- execution-driven


def exec_records(*, copy_name=f"{MARKER} copy of HEALTH:12", test_set_id=COPY, execution=EXECUTION):
    return {
        ("TestSet", COPY): {"id": COPY, "name": copy_name},
        ("TestExecution", execution): {"id": execution, "testSetId": test_set_id},
    }


def exec_payload(**extra):
    return {"objectType": "TestExecution", "projectId": PROJECT, "id": RECORD,
            "testSetId": COPY, "status": "Passed", "executionFinished": "2026-11-16T01:00:00Z", **extra}


def test_live_execution_on_this_runs_copy_passes(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(exec_records(execution=RECORD), jobs=[job("job-1", exec_payload())]))
    expect_ok(capsys, grader.live, seed_for("Finished", "TestExecution"))


def test_live_execution_of_another_test_set_fails(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    other = "66666666-6666-6666-6666-666666666666"
    install(grader, monkeypatch, FakeUip(exec_records(execution=RECORD, test_set_id=other),
                                         jobs=[job("job-1", exec_payload())]))
    out = expect_fail(capsys, grader.live, seed_for("Finished", "TestExecution"))
    assert f"ran test set {other!r}, not this run's copy" in out


def test_live_copy_without_marker_fails(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(exec_records(execution=RECORD, copy_name="HEALTH:12 shared fixture"),
                                         jobs=[job("job-1", exec_payload())]))
    out = expect_fail(capsys, grader.live, seed_for("Updated", "TestExecution"))
    assert "not this run's copy" in out


def test_live_seed_without_copy_id_fails(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip(exec_records(execution=RECORD)))
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestExecution", execution_test_set_id=""))
    assert "no execution_test_set_id" in out


def test_live_execution_not_found_fails(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    install(grader, monkeypatch, FakeUip({("TestSet", COPY): {"id": COPY, "name": MARKER}}))
    out = expect_fail(capsys, grader.live, seed_for("Created", "TestExecution"))
    assert f"TestExecution {RECORD} not found" in out


# ---------------------------------------------------------------- TestCaseLog


def log_payload(**extra):
    return {"objectType": "TestCaseLog", "projectId": PROJECT, "id": RECORD,
            "testExecutionId": EXECUTION, "testCaseId": "77777777-7777-7777-7777-777777777777",
            "result": "Passed", **extra}


def test_live_testcaselog_needs_execution_id_in_result(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox)
    out = expect_fail(capsys, grader.live, seed_for("Finished", "TestCaseLog"))
    assert "no execution_id for a TestCaseLog" in out


def test_live_testcaselog_matching_id_and_execution_passes(grader, sandbox, monkeypatch, capsys):
    write_result(sandbox, execution_id=EXECUTION)
    fake = install(grader, monkeypatch, FakeUip(exec_records(), jobs=[job("job-1", log_payload())]))
    expect_ok(capsys, grader.live, seed_for("Finished", "TestCaseLog"))
    # Ownership is proved through the log's execution, not the log id.
    gets = [a for a in fake.calls if a[:4] == ("is", "resources", "run", "get")]
    assert any(a[5] == "TestExecution" and f"id={EXECUTION}" in a[-1] for a in gets)


@pytest.mark.parametrize(
    "payload",
    [
        log_payload(testExecutionId="88888888-8888-8888-8888-888888888888"),
        log_payload(id="99999999-9999-9999-9999-999999999999"),
    ],
    ids=["other-execution", "other-log"],
)
def test_live_testcaselog_must_match_id_and_execution(grader, sandbox, monkeypatch, capsys, payload):
    write_result(sandbox, execution_id=EXECUTION)
    install(grader, monkeypatch, FakeUip(exec_records(), jobs=[job("job-1", payload)]))
    out = expect_fail(capsys, grader.live, seed_for("Finished", "TestCaseLog"))
    assert "none returned a payload" in out
