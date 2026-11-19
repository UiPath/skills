"""check_cm_golden_run: the opening path of one debug run, with `uip` stubbed.

The plan restates the built CMGoldenExpense opening (stage ids and task
shapes from a real build's artifact): Stage 1 starts on
case-entered and runs agent -> process -> rpa in sequence; Stage 2 is entered
on Stage 1's completion and opens the manager's approval. Debug payloads use
the CLI's `Data` shape (camelCase rows), the instance follow-up uses
`instance element-executions` (PascalCase rows, as the diagnose grader reads).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CASE_ROOT = HERE.parent.parent
sys.path.insert(0, str(CASE_ROOT))
sys.path.insert(0, str(CASE_ROOT / "_setup"))
import case_run  # noqa: E402
from _shared import case_run_path  # noqa: E402


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
    path = case_run_path.opening_path(PLAN)
    assert [t["displayName"] for _, t in path["automated"]] == [
        "Analyze Expense Request", "Process Expense Request", "Record Expense via RPA",
    ]
    assert [s["id"] for s in path["next"]] == ["Stage_7jhjJV"]
    assert path["human"] == []


def test_a_run_parked_at_the_approval_passes() -> None:
    path = case_run_path.opening_path(PLAN)
    assert case_run_path.path_failures(path, {"executions": AT_APPROVAL}) == []


def test_a_run_whose_robot_never_ran_fails() -> None:
    path = case_run_path.opening_path(PLAN)
    rows = [r for r in AT_APPROVAL if r["elementId"] != "tcmH1qeMP"]
    problems = case_run_path.path_failures(path, {"executions": rows})
    assert any("rpa task 'Record Expense via RPA'" in p for p in problems)


def test_a_run_that_never_reached_the_approval_fails() -> None:
    path = case_run_path.opening_path(PLAN)
    problems = case_run_path.path_failures(path, {"executions": STAGE1_DONE})
    assert problems == ["the case never moved on to 'Stage 2'"]


def test_a_failed_required_task_fails() -> None:
    path = case_run_path.opening_path(PLAN)
    rows = AT_APPROVAL + [{"elementId": "tWHwPiWpw", "status": "Faulted"}]
    problems = case_run_path.path_failures(path, {"executions": rows})
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
    monkeypatch.setattr(case_run_path.time, "sleep", lambda s: None)

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

    path, run = case_run_path.run_opening_path(PLAN)

    assert case_run_path.path_failures(path, run) == []
    assert ["uip", "maestro", "case", "instance", "cancel", "inst-1",
            "--comment", "eval cleanup"] in stub.calls


def test_a_poll_timeout_envelope_is_followed_by_its_instance_id(fake) -> None:
    """`ErrorCode: timeout` carries only instanceId and lastStatus."""
    fake(
        {"Result": "Failure", "ErrorCode": "timeout",
         "Data": {"instanceId": "inst-2", "lastStatus": "Running", "timeoutSeconds": 600}},
        follow_up=[{"ElementId": r["elementId"], "Status": r["status"]} for r in AT_APPROVAL],
    )

    path, run = case_run_path.run_opening_path(PLAN)

    assert run["status"] == "Running"
    assert case_run_path.path_failures(path, run) == []


def test_a_debug_that_never_started_an_instance_fails(fake) -> None:
    fake({"Result": "Failure", "Message": "Resource is not configured"}, follow_up=[])

    with pytest.raises(SystemExit, match="did not start an instance"):
        case_run_path.run_opening_path(PLAN)


def test_post_run_cancels_only_the_recorded_debug_instances(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "_setup").mkdir()
    case_run.record_debug_instance("ours")
    cancelled = []

    def uip(args, timeout=120):
        if args[:4] == ["maestro", "case", "instance", "cancel"]:
            cancelled.append(args[4])
            return {"Result": "Success"}
        return {"Result": "Failure"}

    monkeypatch.setattr(case_run, "_uip", uip)

    assert case_run.cancel_debug_instances() == 0
    assert cancelled == ["ours"]


def test_a_tenant_cancelled_debug_is_retried_once(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    import _shared.case_check as case_check

    cancelled = {"Result": "Failure", "Data": {"instanceId": "inst-a", "finalStatus": "Cancelled"}}
    suspended = {"Result": "Failure", "Data": {"instanceId": "inst-b", "finalStatus": "Suspended",
                                                 "elementExecutions": STAGE1_DONE}}
    stub = fake(cancelled, follow_up=[])
    replies = iter([cancelled, suspended])
    run = stub.run

    def run_debug_twice(cmd, timeout, what):
        if cmd[1:4] == ["maestro", "case", "debug"]:
            stub.debug_stdout = next(replies)
        return run(cmd, timeout, what)

    monkeypatch.setattr(case_check, "_run", run_debug_twice)

    result = case_run_path.debug_case()

    assert result["instance_id"] == "inst-b"
    assert sum(1 for c in stub.calls if c[1:4] == ["maestro", "case", "debug"]) == 2


def test_a_second_cancelled_debug_is_returned_not_retried_again(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    cancelled = {"Result": "Failure", "Data": {"instanceId": "inst-a", "finalStatus": "Cancelled"}}
    stub = fake(cancelled, follow_up=[])

    result = case_run_path.debug_case()

    assert result["status"] == "Cancelled"
    assert sum(1 for c in stub.calls if c[1:4] == ["maestro", "case", "debug"]) == 2


def _debug_calls(stub) -> int:
    return sum(1 for c in stub.calls if c[1:4] == ["maestro", "case", "debug"])


def test_a_start_fault_then_a_cancelled_debug_is_two_calls_in_all(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    import _shared.case_check as case_check

    fault = {"Result": "Failure", "Message": "Failed during start-instance: 503 Service Unavailable"}
    cancelled = {"Result": "Failure", "Data": {"instanceId": "inst-a", "finalStatus": "Cancelled"}}
    stub = fake(fault, follow_up=[])
    replies = iter([fault, cancelled, cancelled])
    run = stub.run

    def scripted(cmd, timeout, what):
        if cmd[1:4] == ["maestro", "case", "debug"]:
            stub.debug_stdout = next(replies)
        return run(cmd, timeout, what)

    monkeypatch.setattr(case_check, "_run", scripted)

    result = case_run_path.debug_case()

    assert result["status"] == "Cancelled"
    assert _debug_calls(stub) == case_run_path.MAX_DEBUG_CALLS


def test_a_cancelled_debug_then_a_start_fault_is_two_calls_in_all(fake, monkeypatch: pytest.MonkeyPatch) -> None:
    import _shared.case_check as case_check

    fault = {"Result": "Failure", "Message": "Failed during start-instance: 503 Service Unavailable"}
    cancelled = {"Result": "Failure", "Data": {"instanceId": "inst-a", "finalStatus": "Cancelled"}}
    stub = fake(cancelled, follow_up=[])
    replies = iter([cancelled, fault, fault])
    run = stub.run

    def scripted(cmd, timeout, what):
        if cmd[1:4] == ["maestro", "case", "debug"]:
            stub.debug_stdout = next(replies)
        return run(cmd, timeout, what)

    monkeypatch.setattr(case_check, "_run", scripted)

    with pytest.raises(SystemExit, match="did not start an instance"):
        case_run_path.debug_case()

    assert _debug_calls(stub) == case_run_path.MAX_DEBUG_CALLS


GOLDEN_TASKS = [
    ("cm_golden_expense", "cm_golden_expense.yaml"),
    ("contract_execution", "contract_execution.yaml"),
]
REFRESH_S, FOLLOW_UP_S, CANCEL_S, DEBUG_S = 180, 480, 180, 1500


@pytest.mark.parametrize("folder,name", GOLDEN_TASKS)
def test_the_run_check_timeout_covers_every_debug_call(folder: str, name: str) -> None:
    import yaml

    task = yaml.safe_load((Path(__file__).resolve().parent.parent / folder / name).read_text())
    check = next(c for c in task["success_criteria"] if c.get("command", "").endswith("_run.py"))
    calls = case_run_path.MAX_DEBUG_CALLS
    worst = (REFRESH_S + calls * DEBUG_S + (calls - 1) * case_run_path.RETRY_SLEEP_S
             + FOLLOW_UP_S + CANCEL_S)

    assert check["timeout"] > worst


def test_the_task_timeout_outlasts_the_turn_and_every_criterion() -> None:
    import yaml

    task = yaml.safe_load((Path(__file__).resolve().parent / "cm_golden_expense.yaml").read_text())
    criteria = sum(c.get("timeout", 0) for c in task["success_criteria"])

    assert task["run_limits"]["task_timeout"] > task["run_limits"]["turn_timeout"] + criteria


def _chained(task_id: str, task_type: str, after: list[str], required: bool = True) -> dict:
    return {
        "id": task_id, "type": task_type, "displayName": task_id, "isRequired": required,
        "entryConditions": [{"rules": [[{"rule": "selected-tasks-completed",
                                         "selectedTasksIds": after}]]}],
    }


CHAIN_PLAN = {
    "nodes": [
        {"id": "Stage_a", "type": "case-management:Stage", "data": {
            "label": "Opening",
            "entryConditions": [{"rules": [[{"rule": "case-entered"}]]}],
            "tasks": [
                [_task("tFirst", "http-request", "First", "current-stage-entered")],
                [_chained("tSecond", "script", ["tFirst"])],
                [_chained("tReview", "action", ["tSecond"])],
                [_chained("tAfterReview", "agent", ["tReview"])],
                [_chained("tOptional", "agent", ["tFirst"], required=False)],
            ],
        }},
    ]
}


@pytest.mark.parametrize("task_type", [
    "http-request", "flow-process", "external-agent", "external-workflow",
    "document-extraction", "script",
])
def test_every_non_human_non_waiting_type_is_automated(task_type: str) -> None:
    plan = {"nodes": [{"id": "S", "type": "case-management:Stage", "data": {
        "entryConditions": [{"rules": [[{"rule": "case-entered"}]]}],
        "tasks": [[_task("t1", task_type, "T", "current-stage-entered")]],
    }}]}
    assert [t["id"] for _, t in case_run_path.opening_path(plan)["automated"]] == ["t1"]


@pytest.mark.parametrize("task_type", ["wait-for-timer", "wait-for-connector", "action", "wait-for-user"])
def test_waiting_and_human_types_are_not_automated(task_type: str) -> None:
    plan = {"nodes": [{"id": "S", "type": "case-management:Stage", "data": {
        "entryConditions": [{"rules": [[{"rule": "case-entered"}]]}],
        "tasks": [[_task("t1", task_type, "T", "current-stage-entered")]],
    }}]}
    assert case_run_path.opening_path(plan)["automated"] == []


def test_the_opening_path_follows_selected_tasks_completed_chains() -> None:
    path = case_run_path.opening_path(CHAIN_PLAN)

    assert [t["id"] for _, t in path["automated"]] == ["tFirst", "tSecond"]
    assert [t["id"] for _, t in path["human"]] == ["tReview"]


def test_wait_for_counts_the_time_the_reads_take(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [0.0]
    reads: list[float] = []

    def read(instance_id: str) -> list[dict]:
        clock[0] += 100
        reads.append(clock[0])
        return []

    monkeypatch.setattr(case_run_path.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(case_run_path.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    monkeypatch.setattr(case_run_path, "instance_executions", read)

    case_run_path.wait_for({"executions": [], "status": "Running", "instance_id": "i"},
                           lambda rows: False, budget=480, every=20)

    assert len(reads) == 4
