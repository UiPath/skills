"""check_expense_runnable_run: the path a completed debug run took.

Payload rows have the shape `uip maestro case debug --output json` returns in
`Data.elementExecutions` (elementId / elementType / status).
No tenant is touched.
"""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import re
from pathlib import Path

import pytest
import yaml

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_run", HERE / "check_expense_runnable_run.py")
check_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_run)

from _shared import case_run_path  # noqa: E402

TASK_YAML = HERE / "expense_runnable_e2e.yaml"
RUN_CRITERION_COMMAND = "check_expense_runnable_run.py"
REFRESH_TIMEOUT_S = 180
INSTANCE_READ_S = 120 + 180 + 120
# The last poll reads the instance's executions, then its status; a run that
# ended on that status read then has its executions read as the finished run's.
LAST_POLL_READS = 3

STAGES = {
    "Stage_sub": "Submission",
    "Stage_mgr": "Manager Approval",
    "Stage_fin": "Finance Approval",
    "Stage_pay": "Payment",
    "Stage_ok": "Approved",
    "Stage_rej": "Rejected",
    "Stage_wd": "Withdrawn",
}
PLAN = {
    "nodes": [{"id": "trigger_1", "type": "uipath.case.trigger"}]
    + [
        {"id": sid, "type": "case-management:Stage", "data": {"label": label, "tasks": []}}
        for sid, label in STAGES.items()
    ]
}
HAPPY = ("Stage_sub", "Stage_mgr", "Stage_fin", "Stage_pay", "Stage_ok")


def payload(rows: list[tuple[str, str, str]]) -> dict:
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": e, "elementType": t, "status": s} for e, t, s in rows
        ],
    }


def happy_rows() -> list[tuple[str, str, str]]:
    return [("trigger_1", "StartEvent", "Completed")] + [
        (sid, "CaseStage", "Completed") for sid in HAPPY
    ] + [("tApiTask", "ServiceTask", "Completed")]


def test_accepts_the_approved_path() -> None:
    assert check_run.check_path(PLAN, payload(happy_rows())) == [
        "Submission", "Manager Approval", "Finance Approval", "Payment", "Approved",
    ]


def test_a_skipped_happy_stage_fails() -> None:
    rows = [row for row in happy_rows() if row[0] != "Stage_fin"]
    with pytest.raises(SystemExit, match="'Finance Approval' did not complete"):
        check_run.check_path(PLAN, payload(rows))


def test_a_rejected_lane_that_ran_fails() -> None:
    rows = happy_rows() + [("Stage_rej", "CaseStage", "Completed")]
    with pytest.raises(SystemExit, match="'Rejected' ran on the approved path"):
        check_run.check_path(PLAN, payload(rows))


def test_a_lane_listed_as_not_started_did_not_run() -> None:
    rows = happy_rows() + [("Stage_wd", "CaseStage", "NotStarted")]
    check_run.check_path(PLAN, payload(rows))


def test_a_failed_element_fails_even_when_stages_completed() -> None:
    rows = happy_rows() + [("tRpaTask", "ServiceTask", "Failed")]
    with pytest.raises(SystemExit, match="elements failed during the run"):
        check_run.check_path(PLAN, payload(rows))


def _plan_with_timer(required: bool) -> dict:
    stage = {
        "id": "Stage_mgr", "type": "case-management:Stage",
        "data": {"label": "Manager Approval", "tasks": [[
            {"id": "tTimer", "type": "wait-for-timer", "isRequired": required}
        ]]},
    }
    nodes = [n for n in PLAN["nodes"] if n["id"] != "Stage_mgr"] + [stage]
    return {"nodes": nodes}


def test_a_cancelled_optional_timer_passes() -> None:
    rows = happy_rows() + [("tTimer", "Timer", "Cancelled")]
    assert len(check_run.check_path(_plan_with_timer(False), payload(rows))) == 5


def test_a_cancelled_required_task_fails() -> None:
    rows = happy_rows() + [("tTimer", "Timer", "Cancelled")]
    with pytest.raises(SystemExit, match="elements failed during the run"):
        check_run.check_path(_plan_with_timer(True), payload(rows))


def test_a_faulted_optional_timer_still_fails() -> None:
    rows = happy_rows() + [("tTimer", "Timer", "Faulted")]
    with pytest.raises(SystemExit, match="elements failed during the run"):
        check_run.check_path(_plan_with_timer(False), payload(rows))


def test_pascal_cased_rows_are_read_too() -> None:
    data = {
        "FinalStatus": "Completed",
        "ElementExecutions": [
            {"ElementId": e, "ElementType": t, "Status": s} for e, t, s in happy_rows()
        ],
    }
    assert len(check_run.check_path(PLAN, data)) == 5


# A run on Automation Suite 2.2610: the case completed and every task with it,
# but each stage's own execution stayed InProgress.
AS_RUN = json.loads((HERE / "testdata" / "as_2610_completed_run.json").read_text(encoding="utf-8"))
AS_PLAN = AS_RUN["plan"]


def _as_run(**status_by_name: str | None) -> dict:
    """The recorded run, with a stage's or task's status replaced, or its rows dropped (None)."""
    run = copy.deepcopy(AS_RUN)
    ids = {
        (node.get("data") or {}).get("label"): node["id"]
        for node in AS_PLAN["nodes"] if (node.get("data") or {}).get("label")
    }
    ids.update({
        task["displayName"]: task["id"]
        for node in AS_PLAN["nodes"]
        for lane in (node.get("data") or {}).get("tasks") or []
        for task in lane
    })
    for name, status in status_by_name.items():
        element = ids[name.replace("_", " ")]
        rows = [row for row in run["elementExecutions"] if row["elementId"] == element]
        assert rows, name
        for row in rows:
            if status is None:
                run["elementExecutions"].remove(row)
            else:
                row["status"] = status
    return run


def test_the_recorded_run_left_every_stage_execution_open() -> None:
    by_id = check_run.statuses_by_element(AS_RUN)
    stages = [n["id"] for n in AS_PLAN["nodes"] if (n.get("data") or {}).get("label") in check_run.HAPPY_PATH]

    assert AS_RUN["finalStatus"] == "Completed"
    assert [by_id[stage] for stage in stages] == [["InProgress"]] * 5


def test_a_completed_run_whose_stage_executions_stay_open_passes() -> None:
    assert check_run.check_path(AS_PLAN, AS_RUN) == list(check_run.HAPPY_PATH)


def test_an_open_stage_with_an_unfinished_required_task_fails() -> None:
    with pytest.raises(SystemExit, match=r"'Payment' did not complete .*not completed: \['Payment Confirmation'\]"):
        check_run.check_path(AS_PLAN, _as_run(Payment_Confirmation="InProgress"))


def test_an_open_stage_whose_required_task_never_ran_fails() -> None:
    with pytest.raises(SystemExit, match=r"'Approved' did not complete .*\['Update GL Records'\]"):
        check_run.check_path(AS_PLAN, _as_run(Update_GL_Records=None))


def test_an_open_stage_does_not_wait_on_its_optional_task() -> None:
    run = _as_run(Approval_Escalation=None)

    assert len(check_run.check_path(AS_PLAN, run)) == 5


def test_an_open_stage_that_was_never_entered_fails() -> None:
    with pytest.raises(SystemExit, match="'Finance Approval' did not complete .*never entered"):
        check_run.check_path(AS_PLAN, _as_run(Finance_Approval=None))


@pytest.mark.parametrize("final_status", ["", "Running", "Suspended"])
def test_open_stage_executions_fail_when_the_run_is_not_reported_completed(final_status: str) -> None:
    run = {**_as_run(), "finalStatus": final_status}

    with pytest.raises(SystemExit, match="'Submission' did not complete"):
        check_run.check_path(AS_PLAN, run)


NEVER_STARTED = ["NotStarted", "Pending", "Skipped", ""]
ENDED_WITHOUT_COMPLETING = ["Terminated", "Exited", "Stopped"]


@pytest.mark.parametrize("status", NEVER_STARTED + ENDED_WITHOUT_COMPLETING)
def test_only_a_stage_execution_left_in_progress_is_read_from_the_run(status: str) -> None:
    with pytest.raises(SystemExit, match="'Finance Approval' did not complete"):
        check_run.check_path(AS_PLAN, _as_run(Finance_Approval=status))


@pytest.mark.parametrize("status", NEVER_STARTED + ENDED_WITHOUT_COMPLETING)
def test_one_stage_not_left_in_progress_fails_beside_completed_stages(status: str) -> None:
    others = {name: "Completed" for name in ("Submission", "Manager_Approval", "Payment", "Approved")}

    with pytest.raises(SystemExit, match="'Finance Approval' did not complete"):
        check_run.check_path(AS_PLAN, _as_run(Finance_Approval=status, **others))


def _with_another_stage_execution(run: dict, stage: str, status: str, *, first: bool) -> dict:
    """``run`` with one more execution row of ``stage``, before or after its recorded one."""
    stage_id = next(n["id"] for n in AS_PLAN["nodes"] if (n.get("data") or {}).get("label") == stage)
    row = {"elementId": stage_id, "elementType": "CaseStage", "status": status}
    rows = run["elementExecutions"]
    at = next(i for i, r in enumerate(rows) if r["elementId"] == stage_id)
    rows.insert(at if first else at + 1, row)
    return run


@pytest.mark.parametrize("status", ENDED_WITHOUT_COMPLETING + ["NotStarted"])
@pytest.mark.parametrize("first", [True, False])
def test_a_stage_with_an_execution_that_is_not_in_progress_is_not_read_from_the_run(status: str, first: bool) -> None:
    run = _with_another_stage_execution(_as_run(), "Submission", status, first=first)

    with pytest.raises(SystemExit, match="'Submission' did not complete"):
        check_run.check_path(AS_PLAN, run)


def test_a_stage_entered_twice_and_left_in_progress_both_times_is_read_from_the_run() -> None:
    run = _with_another_stage_execution(_as_run(), "Submission", "InProgress", first=False)

    assert len(check_run.check_path(AS_PLAN, run)) == 5


def test_a_stage_with_one_completed_execution_passes_whatever_its_other_executions() -> None:
    run = _with_another_stage_execution(_as_run(), "Submission", "Completed", first=False)

    assert len(check_run.check_path(AS_PLAN, run)) == 5


@pytest.mark.parametrize("status", ["Faulted", "Failed", "Cancelled"])
def test_a_stage_execution_that_failed_fails_as_a_failed_element(status: str) -> None:
    with pytest.raises(SystemExit, match="elements failed during the run"):
        check_run.check_path(AS_PLAN, _as_run(Finance_Approval=status))


def _as_plan(**required_by_task: bool | None) -> dict:
    """The recorded plan, with a task's ``isRequired`` replaced, or removed (None)."""
    plan = copy.deepcopy(AS_PLAN)
    tasks = {
        task["displayName"]: task
        for node in plan["nodes"]
        for lane in (node.get("data") or {}).get("tasks") or []
        for task in lane
    }
    for name, required in required_by_task.items():
        task = tasks[name.replace("_", " ")]
        if required is None:
            del task["isRequired"]
        else:
            task["isRequired"] = required
    return plan


def test_a_plan_that_marks_the_designs_required_tasks_optional_does_not_pass_on_its_own_flags() -> None:
    # The design requires both Approved tasks; the plan under grading cannot waive them.
    plan = _as_plan(Send_Approval_Confirmation=False, Update_GL_Records=False)
    run = _as_run(Send_Approval_Confirmation=None, Update_GL_Records=None)

    with pytest.raises(
        SystemExit,
        match=r"'Approved' did not complete .*\['Send Approval Confirmation', 'Update GL Records'\]",
    ):
        check_run.check_path(plan, run)


@pytest.mark.parametrize("flag", [False, None])
def test_a_required_task_that_did_not_run_fails_whatever_the_plans_flag_says(flag: bool | None) -> None:
    plan = _as_plan(Update_GL_Records=flag)

    with pytest.raises(SystemExit, match=r"'Approved' did not complete .*\['Update GL Records'\]"):
        check_run.check_path(plan, _as_run(Update_GL_Records=None))


def test_a_required_task_the_plan_lacks_counts_as_not_completed() -> None:
    plan = copy.deepcopy(AS_PLAN)
    for node in plan["nodes"]:
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in lane:
                if task["displayName"] == "Payment Confirmation":
                    task["displayName"] = "Confirm Payment"

    with pytest.raises(SystemExit, match=r"'Payment' did not complete .*\['Payment Confirmation'\]"):
        check_run.check_path(plan, AS_RUN)


def _as_plan_with(rename: dict[str, str] | None = None, move: tuple[str, str] | None = None) -> dict:
    """The recorded plan, with tasks renamed, or one task moved to another stage."""
    plan = copy.deepcopy(AS_PLAN)
    stages = {(node.get("data") or {}).get("label"): node for node in plan["nodes"]}
    for node in plan["nodes"]:
        for lane in (node.get("data") or {}).get("tasks") or []:
            for task in list(lane):
                task["displayName"] = (rename or {}).get(task["displayName"], task["displayName"])
                if move and task["displayName"] == move[0]:
                    lane.remove(task)
                    stages[move[1]]["data"]["tasks"].append([task])
    return plan


def test_a_required_task_that_completed_in_another_stage_does_not_count_for_its_own() -> None:
    plan = _as_plan_with(move=("Update GL Records", "Payment"))

    with pytest.raises(SystemExit, match=r"'Approved' did not complete .*\['Update GL Records'\]"):
        check_run.check_path(plan, AS_RUN)


def test_a_required_task_is_found_whatever_the_case_and_punctuation_of_its_name() -> None:
    plan = _as_plan_with(rename={
        "Update GL Records": "update-GL records",
        "Budget & GL Reconciliation": "Budget GL reconciliation",
    })

    assert len(check_run.check_path(plan, AS_RUN)) == 5


def test_a_cancelled_task_the_design_requires_fails_though_the_plan_marks_it_optional() -> None:
    plan = _as_plan(Update_GL_Records=False)
    run = _as_run(Update_GL_Records="Cancelled", Approved="Completed")

    with pytest.raises(SystemExit, match="elements failed during the run"):
        check_run.check_path(plan, run)


def test_the_plans_optional_flag_on_a_task_the_design_does_not_require_changes_nothing() -> None:
    plan = _as_plan(Approval_Escalation=True)

    assert len(check_run.check_path(plan, _as_run(Approval_Escalation=None))) == 5


def test_the_required_tasks_are_the_ones_the_design_document_marks_required() -> None:
    """SDD_REQUIRED_TASKS is fixtures/sdd.md's `Required: Yes` rows, stage by stage."""
    required: dict[str, list[str]] = {}
    stage, in_table = None, False
    for line in (HERE / "fixtures" / "sdd.md").read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^### Stage \d+: (.+)$", line)
        if heading:
            stage, in_table = heading.group(1).strip(), False
        elif line.startswith("#### Tasks"):
            in_table = True
        elif line.startswith("#####"):
            in_table = False
        elif in_table and line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells[0].isdigit() and cells[3] == "Yes":
                required.setdefault(stage, []).append(cells[1])

    assert {name: tuple(required[name]) for name in check_run.HAPPY_PATH} == check_run.SDD_REQUIRED_TASKS


def test_a_stage_whose_execution_completed_is_not_judged_by_its_tasks() -> None:
    plan = _plan_with_timer(True)
    rows = happy_rows() + [("tTimer", "Timer", "InProgress")]

    assert len(check_run.check_path(plan, payload(rows))) == 5


def _stub_run(monkeypatch: pytest.MonkeyPatch, start: dict, reads: list[list[dict]]):
    from _shared import case_run_path

    monkeypatch.setattr(check_run, "existing_caseplan", lambda _p: "plan")
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: PLAN)
    monkeypatch.setattr(check_run, "debug_case", lambda timeout: dict(start))
    pending = list(reads)
    monkeypatch.setattr(case_run_path, "instance_executions", lambda _i: pending.pop(0))
    monkeypatch.setattr(check_run, "instance_executions", lambda _i: pending.pop(0))
    monkeypatch.setattr(case_run_path.time, "sleep", lambda _s: None)
    return _stub_instance_status(monkeypatch, [])


def _stub_instance_status(monkeypatch: pytest.MonkeyPatch, statuses: list[str]) -> list[str]:
    """The instance reports ``statuses`` in turn, then Running. Returns the ids asked about."""
    asked: list[str] = []
    upcoming = list(statuses)

    def status_of_instance(instance_id: str) -> str:
        asked.append(instance_id)
        return upcoming.pop(0) if upcoming else "Running"

    monkeypatch.setattr(check_run, "instance_status", status_of_instance)
    return asked


def _rows(rows: list[tuple[str, str, str]]) -> list[dict]:
    return payload(rows)["elementExecutions"]


def test_a_cli_timeout_is_followed_to_the_completed_instance(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": []}
    partial = _rows(happy_rows()[:3])
    _stub_run(monkeypatch, started, [partial, _rows(happy_rows())])

    check_run.main()

    assert "OK: the Approved stage completed" in capsys.readouterr().out


def test_a_cli_timeout_whose_instance_faults_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": []}
    faulted = _rows(happy_rows()[:2] + [("tRpaTask", "ServiceTask", "Faulted")])
    _stub_run(monkeypatch, started, [faulted])

    with pytest.raises(SystemExit, match="elements failed during the run"):
        check_run.main()


def test_an_instance_that_never_finishes_fails_on_the_path(monkeypatch: pytest.MonkeyPatch) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": []}
    stuck = _rows(happy_rows()[:3])
    _stub_run(monkeypatch, started, [stuck] * 200)
    monkeypatch.setattr(check_run, "WAIT_BUDGET_S", 0)

    with pytest.raises(SystemExit, match="did not complete in the run"):
        check_run.main()


def test_a_run_the_cli_reports_completed_is_checked_as_is(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    started = {"status": "Completed", "instance_id": "i-1", "executions": _rows(happy_rows())}
    asked = _stub_run(monkeypatch, started, [])

    check_run.main()

    assert "OK:" in capsys.readouterr().out
    assert asked == []  # the CLI reported the run's end; the instance is not asked again


def test_a_run_the_cli_reports_completed_passes_with_open_stage_executions(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    started = {"status": "Completed", "instance_id": "i-1", "executions": AS_RUN["elementExecutions"]}
    _stub_run(monkeypatch, started, [])
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)

    check_run.main()

    assert "OK: the Approved stage completed" in capsys.readouterr().out


def _stub_cli_timeout_on_open_stages(monkeypatch: pytest.MonkeyPatch, statuses: list[str], reads: int) -> list[str]:
    """The CLI stopped polling; the instance leaves its stage executions open on every read."""
    started = {"status": "", "instance_id": "i-1", "executions": []}
    _stub_run(monkeypatch, started, [AS_RUN["elementExecutions"]] * reads)
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)
    return _stub_instance_status(monkeypatch, statuses)


def test_a_run_that_goes_from_running_to_completed_with_open_stage_executions_passes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    # Running on the first two polls, then Completed: the wait ends, then one read of the finished run's executions.
    asked = _stub_cli_timeout_on_open_stages(monkeypatch, ["Running", "Running", "Completed"], reads=3)

    check_run.main()

    assert asked == ["i-1"] * 3
    assert "OK: the Approved stage completed" in capsys.readouterr().out


def test_the_executions_graded_are_read_after_the_instance_ended(monkeypatch: pytest.MonkeyPatch) -> None:
    # The read before the instance's end still shows a required task running; the one after it does not.
    started = {"status": "", "instance_id": "i-1", "executions": []}
    before = _as_run(Update_GL_Records="InProgress")["elementExecutions"]
    _stub_run(monkeypatch, started, [before, AS_RUN["elementExecutions"]])
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)
    _stub_instance_status(monkeypatch, ["Running", "Completed"])

    check_run.main()


def test_a_cli_timeout_whose_instance_never_ends_fails_on_the_open_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": AS_RUN["elementExecutions"]}
    _stub_run(monkeypatch, started, [])
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)
    monkeypatch.setattr(check_run, "WAIT_BUDGET_S", 0)

    with pytest.raises(SystemExit, match="'Submission' did not complete"):
        check_run.main()


def test_an_instance_that_ends_as_the_budget_runs_out_is_still_read_as_ended(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": AS_RUN["elementExecutions"]}
    _stub_run(monkeypatch, started, [AS_RUN["elementExecutions"]])
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)
    monkeypatch.setattr(check_run, "WAIT_BUDGET_S", 0)
    _stub_instance_status(monkeypatch, ["Completed"])

    check_run.main()

    assert "OK: the Approved stage completed" in capsys.readouterr().out


def test_a_required_task_that_completes_as_the_budget_runs_out_is_read_as_completed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    # The status read that shows the end uses up the budget; the executions in hand predate it.
    before = _as_run(Update_GL_Records="InProgress")["elementExecutions"]
    started = {"status": "", "instance_id": "i-1", "executions": before}
    _stub_run(monkeypatch, started, [AS_RUN["elementExecutions"]])
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)
    monkeypatch.setattr(check_run, "WAIT_BUDGET_S", 0)
    _stub_instance_status(monkeypatch, ["Completed"])

    check_run.main()

    assert "OK: the Approved stage completed" in capsys.readouterr().out


@pytest.mark.parametrize("in_hand", [
    _as_run(Update_GL_Records="InProgress")["elementExecutions"],  # stale: the task completed after this read
    AS_RUN["elementExecutions"],  # would pass, but was not read after the end
])
def test_an_ended_run_whose_last_read_returns_nothing_fails_on_the_missing_read(
    monkeypatch: pytest.MonkeyPatch, in_hand: list[dict]
) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": []}
    _stub_run(monkeypatch, started, [in_hand, []])
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)
    _stub_instance_status(monkeypatch, ["Running", "Completed"])

    with pytest.raises(SystemExit, match="ended Completed, but its element executions could not be read"):
        check_run.main()


@pytest.mark.parametrize("status", ["Stopped", "stopped"])
def test_a_stopped_run_fails_though_every_happy_path_stage_completed(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    started = {"status": status, "instance_id": "i-1", "executions": _rows(happy_rows())}
    _stub_run(monkeypatch, started, [])

    with pytest.raises(SystemExit, match=f"finalStatus={status}"):
        check_run.main()


@pytest.mark.parametrize("instance_status", ["Stopped", "Suspended", "Faulted", "Cancelled"])
def test_an_instance_that_did_not_complete_fails_though_its_stage_rows_show_completed(
    monkeypatch: pytest.MonkeyPatch, instance_status: str
) -> None:
    # The CLI stopped polling; every happy-path stage row shows Completed, which would end the wait.
    started = {"status": "", "instance_id": "i-1", "executions": _rows(happy_rows())}
    _stub_run(monkeypatch, started, [])
    asked = _stub_instance_status(monkeypatch, [instance_status])

    with pytest.raises(SystemExit, match=f"finalStatus={instance_status}"):
        check_run.main()
    assert asked == ["i-1"]


def test_a_run_the_cli_reports_suspended_fails_though_its_stage_rows_show_completed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = {"status": "Suspended", "instance_id": "i-1", "executions": _rows(happy_rows())}
    _stub_run(monkeypatch, started, [])
    _stub_instance_status(monkeypatch, ["Running"])

    with pytest.raises(SystemExit, match="finalStatus=Suspended"):
        check_run.main()


def test_a_run_the_cli_reports_suspended_passes_once_its_instance_completes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    started = {"status": "Suspended", "instance_id": "i-1", "executions": _rows(happy_rows()[:3])}
    _stub_run(monkeypatch, started, [_rows(happy_rows())])
    _stub_instance_status(monkeypatch, ["Completed"])

    check_run.main()

    assert "OK: the Approved stage completed" in capsys.readouterr().out


def test_the_instance_status_is_read_before_a_completed_final_stage_ends_the_wait(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": _rows(happy_rows())}
    asked = _stub_run(monkeypatch, started, [])

    check_run.main()

    assert "OK: the Approved stage completed" in capsys.readouterr().out
    assert asked == ["i-1"]


def test_completed_stage_rows_do_not_pass_a_run_whose_status_cannot_be_read(monkeypatch: pytest.MonkeyPatch) -> None:
    # A failed status lookup returns nothing; the rows show every happy-path stage Completed.
    started = {"status": "", "instance_id": "i-1", "executions": _rows(happy_rows())}
    _stub_run(monkeypatch, started, [_rows(happy_rows())] * 3)
    monkeypatch.setattr(check_run, "WAIT_BUDGET_S", 0)
    asked = _stub_instance_status(monkeypatch, [""])

    with pytest.raises(SystemExit, match="status of instance i-1 could not be read, so the run cannot be graded"):
        check_run.main()
    assert asked == ["i-1"]


def test_a_status_that_cannot_be_read_is_read_again_on_the_next_poll(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": _rows(happy_rows())}
    _stub_run(monkeypatch, started, [_rows(happy_rows())])
    asked = _stub_instance_status(monkeypatch, ["", "Running"])

    check_run.main()

    assert "OK: the Approved stage completed" in capsys.readouterr().out
    assert asked == ["i-1"] * 2


def test_a_stopped_instance_whose_first_status_read_failed_still_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": _rows(happy_rows())}
    _stub_run(monkeypatch, started, [_rows(happy_rows())])
    _stub_instance_status(monkeypatch, ["", "Stopped"])

    with pytest.raises(SystemExit, match="finalStatus=Stopped"):
        check_run.main()


def test_open_stage_rows_with_a_status_that_cannot_be_read_fail_on_the_status(monkeypatch: pytest.MonkeyPatch) -> None:
    started = {"status": "", "instance_id": "i-1", "executions": AS_RUN["elementExecutions"]}
    _stub_run(monkeypatch, started, [])
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: AS_PLAN)
    monkeypatch.setattr(check_run, "WAIT_BUDGET_S", 0)
    _stub_instance_status(monkeypatch, [""])

    with pytest.raises(SystemExit, match="could not be read, so the run cannot be graded"):
        check_run.main()


def test_a_cli_timeout_whose_instance_was_stopped_fails_on_its_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_cli_timeout_on_open_stages(monkeypatch, ["Stopped"], reads=0)

    with pytest.raises(SystemExit, match="finalStatus=Stopped"):
        check_run.main()


def test_a_cli_timeout_whose_instance_faulted_fails_on_its_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_cli_timeout_on_open_stages(monkeypatch, ["Faulted"], reads=1)

    with pytest.raises(SystemExit, match="finalStatus=Faulted"):
        check_run.main()


def test_a_run_ending_in_a_non_completed_status_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    started = {"status": "Faulted", "instance_id": "i-1", "executions": _rows(happy_rows()[:2])}
    _stub_run(monkeypatch, started, [])

    with pytest.raises(SystemExit, match="finalStatus=Faulted"):
        check_run.main()


def test_the_run_criterion_timeout_covers_the_worst_case_grader_run() -> None:
    task = yaml.safe_load(TASK_YAML.read_text(encoding="utf-8"))
    criterion = next(c for c in task["success_criteria"] if RUN_CRITERION_COMMAND in c.get("command", ""))
    poll_s = inspect.signature(case_run_path.wait_for).parameters["every"].default
    worst_case_s = (
        REFRESH_TIMEOUT_S
        + case_run_path.MAX_DEBUG_CALLS * check_run.DEBUG_TIMEOUT_S
        + case_run_path.RETRY_SLEEP_S
        + check_run.WAIT_BUDGET_S
        + poll_s
        + LAST_POLL_READS * INSTANCE_READ_S
    )

    assert criterion["timeout"] >= worst_case_s


def test_the_run_criterion_names_the_stage_it_waits_for_not_the_final_status() -> None:
    task = yaml.safe_load(TASK_YAML.read_text(encoding="utf-8"))
    criterion = next(c for c in task["success_criteria"] if RUN_CRITERION_COMMAND in c.get("command", ""))

    assert f"{check_run.FINAL_STAGE} stage completes" in criterion["description"]
    assert "finalStatus=Completed" not in criterion["description"]
