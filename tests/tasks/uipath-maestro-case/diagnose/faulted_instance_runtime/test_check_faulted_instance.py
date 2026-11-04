"""`check_faulted_instance.truth()` maps each open incident to the task it is about.

Cloud raises a case task's incident on the task element; Automation Suite raises it on
the ``tasksEventSubProcess`` wrapper and records the failed task only in the element
executions. The grader must name the task either way, and must not read element
executions when the incident already names a task. ``uip`` is stubbed.
"""

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FOLDER = "Shared/OutcomeExpenseApproval"
TASK_ID = "tQ4kfr50O"


@pytest.fixture
def grader():
    spec = importlib.util.spec_from_file_location("check_faulted_instance", HERE / "check_faulted_instance.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stub(grader, monkeypatch, element_id, executions):
    calls = []

    def fake(*args):
        calls.append(args[:4])
        if args[:4] == ("maestro", "case", "processes", "list"):
            return {"Processes": [{"FolderName": FOLDER, "PackageId": "OutcomeExpenseApproval.Case.X", "ProcessKey": "p", "FolderKey": "f"}]}
        if args[:4] == ("maestro", "case", "instance", "list"):
            return [{
                "InstanceId": "i1",
                "LatestRunStatus": "Faulted",
                "Incidents": [{"IncidentStatus": "Open", "ErrorCode": 400300, "ElementId": element_id}],
            }]
        if args[:4] == ("maestro", "case", "instance", "asset"):
            return {"Nodes": [{"Data": {"Tasks": [[{"Id": TASK_ID, "DisplayName": "Post ledger entry"}]]}}]}
        if args[:4] == ("maestro", "case", "instance", "element-executions"):
            return {"ElementExecutions": executions}
        raise AssertionError(f"unexpected uip call {args}")

    monkeypatch.setattr(grader, "uip", fake)
    return calls


def test_an_incident_on_the_task_names_it_without_reading_executions(grader, monkeypatch):
    calls = _stub(grader, monkeypatch, TASK_ID, executions=[])

    assert grader.truth() == {"i1": [{"errorCode": "400300", "taskNames": ["Post ledger entry"], "elementId": TASK_ID}]}
    assert ("maestro", "case", "instance", "element-executions") not in calls


def test_an_incident_on_the_wrapper_names_the_failed_task_inside_it(grader, monkeypatch):
    _stub(grader, monkeypatch, "tasksEventSubProcess", executions=[
        {"ElementId": "tasksEventSubProcess", "Status": "Failed", "ParentElementId": None},
        {"ElementId": TASK_ID, "Status": "Failed", "ParentElementId": "tasksEventSubProcess"},
        {"ElementId": "other", "Status": "Completed", "ParentElementId": "tasksEventSubProcess"},
    ])

    assert grader.truth()["i1"][0]["taskNames"] == ["Post ledger entry"]


def test_a_completed_task_under_the_wrapper_is_not_the_answer(grader, monkeypatch):
    _stub(grader, monkeypatch, "tasksEventSubProcess", executions=[
        {"ElementId": TASK_ID, "Status": "Completed", "ParentElementId": "tasksEventSubProcess"},
    ])

    assert grader.truth()["i1"][0]["taskNames"] == []


def test_camel_cased_executions_are_read_too(grader, monkeypatch):
    # A CLI that camelCases the payload must grade the same as one that PascalCases it.
    calls = _stub(grader, monkeypatch, "tasksEventSubProcess", executions=[])
    camel = [{"elementId": TASK_ID, "status": "Failed", "parentElementId": "tasksEventSubProcess"}]
    real = grader.uip

    def fake(*args):
        if args[:4] == ("maestro", "case", "instance", "element-executions"):
            return {"elementExecutions": camel}
        return real(*args)

    monkeypatch.setattr(grader, "uip", fake)

    assert grader.truth()["i1"][0]["taskNames"] == ["Post ledger entry"]
    assert calls
