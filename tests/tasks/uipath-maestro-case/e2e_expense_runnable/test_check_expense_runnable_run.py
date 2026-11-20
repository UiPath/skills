"""check_expense_runnable_run: the path a completed debug run took.

Payload rows have the shape `uip maestro case debug --output json` returns in
`Data.elementExecutions` (elementId / elementType / status).
No tenant is touched.
"""

from __future__ import annotations

import importlib.util
import inspect
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


def _stub_run(monkeypatch: pytest.MonkeyPatch, start: dict, reads: list[list[dict]]):
    from _shared import case_run_path

    monkeypatch.setattr(check_run, "existing_caseplan", lambda _p: "plan")
    monkeypatch.setattr(check_run, "read_caseplan", lambda _p: PLAN)
    monkeypatch.setattr(check_run, "debug_case", lambda timeout: dict(start))
    pending = list(reads)
    monkeypatch.setattr(case_run_path, "instance_executions", lambda _i: pending.pop(0))
    monkeypatch.setattr(case_run_path.time, "sleep", lambda _s: None)


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
    _stub_run(monkeypatch, started, [])

    check_run.main()

    assert "OK:" in capsys.readouterr().out


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
        + INSTANCE_READ_S
    )

    assert criterion["timeout"] >= worst_case_s


def test_the_run_criterion_names_the_stage_it_waits_for_not_the_final_status() -> None:
    task = yaml.safe_load(TASK_YAML.read_text(encoding="utf-8"))
    criterion = next(c for c in task["success_criteria"] if RUN_CRITERION_COMMAND in c.get("command", ""))

    assert f"{check_run.FINAL_STAGE} stage completes" in criterion["description"]
    assert "finalStatus=Completed" not in criterion["description"]
