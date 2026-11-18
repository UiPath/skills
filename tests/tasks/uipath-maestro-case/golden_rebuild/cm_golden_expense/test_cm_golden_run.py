"""check_cm_golden_run: the opening path of one debug run, with `uip` stubbed.

The plan restates the built CMGoldenExpense opening (stage ids and task
shapes from the 2026-11-18_04-25-00 artifact): Stage 1 starts on
case-entered and runs agent -> process -> rpa in sequence; Stage 2 is entered
on Stage 1's completion and opens the manager's approval. Debug payloads use
the CLI's `Data` shape (camelCase rows), the instance follow-up uses
`instance element-executions` (PascalCase rows, as the diagnose grader reads).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("case_run_cm", HERE / "_setup" / "case_run.py")
case_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(case_run)


def _task(task_id: str, task_type: str, name: str, rule: str, required: bool = True) -> dict:
    return {
        "id": task_id, "type": task_type, "displayName": name, "isRequired": required,
        "entryConditions": [{"rules": [[{"rule": rule}]]}],
    }


PLAN = {
    "nodes": [
        {"id": "trigger_1", "type": "uipath.case.trigger"},
        {"id": "Stage_ydR2Tr", "type": "case-management:Stage", "data": {
            "label": "Stage 1",
            "entryConditions": [{"rules": [[{"rule": "case-entered"}]]}],
            "tasks": [
                [_task("tvH0saaTv", "agent", "Analyze Expense Request", "runs-sequentially")],
                [_task("tWHwPiWpw", "process", "Process Expense Request", "runs-sequentially")],
                [_task("tcmH1qeMP", "rpa", "Record Expense via RPA", "runs-sequentially")],
            ],
        }},
        {"id": "Stage_7jhjJV", "type": "case-management:Stage", "data": {
            "label": "Stage 2",
            "entryConditions": [{"rules": [[{"rule": "selected-stage-completed",
                                             "selectedStageIds": ["Stage_ydR2Tr"]}]]}],
            "tasks": [[_task("tZUgazYMh", "action", "Manager Approval", "current-stage-entered")]],
        }},
    ]
}
STAGE1_DONE = [
    {"elementId": "trigger_1", "elementType": "StartEvent", "status": "Completed"},
    {"elementId": "Stage_ydR2Tr", "elementType": "CaseStage", "status": "Completed"},
    {"elementId": "tvH0saaTv", "elementType": "ServiceTask", "status": "Completed"},
    {"elementId": "tWHwPiWpw", "elementType": "ServiceTask", "status": "Completed"},
    {"elementId": "tcmH1qeMP", "elementType": "ServiceTask", "status": "Completed"},
]
AT_APPROVAL = STAGE1_DONE + [
    {"elementId": "Stage_7jhjJV", "elementType": "CaseStage", "status": "InProgress"},
    {"elementId": "tZUgazYMh", "elementType": "UserTask", "status": "InProgress"},
]


def test_the_plan_names_the_opening_path() -> None:
    path = case_run.opening_path(PLAN)
    assert [t["displayName"] for _, t in path["automated"]] == [
        "Analyze Expense Request", "Process Expense Request", "Record Expense via RPA",
    ]
    assert [s["id"] for s in path["next"]] == ["Stage_7jhjJV"]
    assert path["human"] == []


def test_a_run_parked_at_the_approval_passes() -> None:
    path = case_run.opening_path(PLAN)
    assert case_run.path_failures(path, {"executions": AT_APPROVAL}) == []


def test_a_run_whose_robot_never_ran_fails() -> None:
    path = case_run.opening_path(PLAN)
    rows = [r for r in AT_APPROVAL if r["elementId"] != "tcmH1qeMP"]
    problems = case_run.path_failures(path, {"executions": rows})
    assert any("rpa task 'Record Expense via RPA'" in p for p in problems)


def test_a_run_that_never_reached_the_approval_fails() -> None:
    path = case_run.opening_path(PLAN)
    problems = case_run.path_failures(path, {"executions": STAGE1_DONE})
    assert problems == ["the case never moved on to 'Stage 2'"]


def test_a_failed_required_task_fails() -> None:
    path = case_run.opening_path(PLAN)
    rows = AT_APPROVAL + [{"elementId": "tWHwPiWpw", "status": "Faulted"}]
    problems = case_run.path_failures(path, {"executions": rows})
    assert any("required elements failed" in p for p in problems)


class FakeUip:
    """Answers `uip ... --output json` calls the way the CLI does."""

    def __init__(self, debug_stdout: dict, follow_up: list[dict]):
        self.debug_stdout = debug_stdout
        self.follow_up = follow_up
        self.calls: list[list[str]] = []

    def run(self, cmd, timeout, what):  # case_check._run signature
        self.calls.append(list(cmd))
        is_debug = cmd[1:4] == ["maestro", "case", "debug"]

        class Done:
            returncode = 1 if is_debug else 0
            stdout = json.dumps(self.debug_stdout if is_debug else {"Result": "Success"})
            stderr = ""

        return Done()

    def uip(self, args, timeout=120):
        self.calls.append(["uip", *args])
        if args[:4] == ["maestro", "case", "instance", "element-executions"]:
            return {"Result": "Success", "Data": {"ElementExecutions": self.follow_up}}
        if args[:4] == ["maestro", "case", "instance", "cancel"]:
            return {"Result": "Success"}
        return {"Result": "Failure"}


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    import _shared.case_check as case_check

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(case_check, "find_project_dir", lambda *a, **k: "Sol/Case")
    monkeypatch.setattr(case_check, "find_solution_dir", lambda *a, **k: "Sol")
    monkeypatch.setattr(case_run.time, "sleep", lambda s: None)

    def install(debug_stdout: dict, follow_up: list[dict]) -> FakeUip:
        stub = FakeUip(debug_stdout, follow_up)
        monkeypatch.setattr(case_check, "_run", stub.run)
        monkeypatch.setattr(case_run, "_uip", stub.uip)
        return stub

    return install


def test_a_suspended_debug_is_followed_on_the_instance_then_cancelled(fake) -> None:
    """The CLI stops at the job's first suspension, before the robot finished."""
    stub = fake(
        {"Result": "Failure", "Code": "CaseDebug", "ErrorCode": "execution_failed",
         "Data": {"instanceId": "inst-1", "finalStatus": "Suspended",
                  "elementExecutions": STAGE1_DONE[:3]}},
        follow_up=[{"ElementId": r["elementId"], "Status": r["status"]} for r in AT_APPROVAL],
    )

    path, run = case_run.run_opening_path(PLAN)

    assert case_run.path_failures(path, run) == []
    assert ["uip", "maestro", "case", "instance", "cancel", "inst-1",
            "--comment", "eval cleanup"] in stub.calls


def test_a_poll_timeout_envelope_is_followed_by_its_instance_id(fake) -> None:
    """`ErrorCode: timeout` carries only instanceId and lastStatus."""
    fake(
        {"Result": "Failure", "ErrorCode": "timeout",
         "Data": {"instanceId": "inst-2", "lastStatus": "Running", "timeoutSeconds": 600}},
        follow_up=[{"ElementId": r["elementId"], "Status": r["status"]} for r in AT_APPROVAL],
    )

    path, run = case_run.run_opening_path(PLAN)

    assert run["status"] == "Running"
    assert case_run.path_failures(path, run) == []


def test_a_debug_that_never_started_an_instance_fails(fake) -> None:
    fake({"Result": "Failure", "Message": "Resource is not configured"}, follow_up=[])

    with pytest.raises(SystemExit, match="did not start an instance"):
        case_run.run_opening_path(PLAN)


def test_post_run_cancels_only_this_tasks_open_debug_instances(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_setup").mkdir()
    (tmp_path / "_setup" / ".tenant-ids.map.json").write_text("{}")
    plan_dir = tmp_path / "CMGoldenExpense" / "CMGoldenExpense"
    plan_dir.mkdir(parents=True)
    (plan_dir / "caseplan.case").write_text(json.dumps(PLAN))
    listing = [
        {"InstanceId": "ours", "Source": "Studio Web Debug", "CreatedTimeUtc": "2999-01-01T00:00:00",
         "LatestRunStatus": "Running", "FolderKey": "f"},
        {"InstanceId": "theirs", "Source": "Studio Web Debug", "CreatedTimeUtc": "2999-01-01T00:00:00",
         "LatestRunStatus": "Running", "FolderKey": "f"},
        {"InstanceId": "old", "Source": "Studio Web Debug", "CreatedTimeUtc": "2000-01-01T00:00:00",
         "LatestRunStatus": "Running", "FolderKey": "f"},
        {"InstanceId": "done", "Source": "Studio Web Debug", "CreatedTimeUtc": "2999-01-01T00:00:00",
         "LatestRunStatus": "Completed", "FolderKey": "f"},
    ]
    cancelled = []

    def uip(args, timeout=120):
        if args[:4] == ["maestro", "case", "instance", "list"]:
            return {"Result": "Success", "Data": listing}
        if args[:4] == ["maestro", "case", "instance", "element-executions"]:
            element = "Stage_ydR2Tr" if args[4] == "ours" else "Stage_someoneElse"
            return {"Result": "Success", "Data": {"ElementExecutions": [{"ElementId": element}]}}
        if args[:4] == ["maestro", "case", "instance", "cancel"]:
            cancelled.append(args[4])
            return {"Result": "Success"}
        return {"Result": "Failure"}

    monkeypatch.setattr(case_run, "_uip", uip)

    assert case_run.cancel_debug_instances() == 0
    assert cancelled == ["ours"]
