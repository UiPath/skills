"""check_expense_runnable_run: the path a completed debug run took.

Payload rows have the shape `uip maestro case debug --output json` returns in
`Data.elementExecutions` (elementId / elementType / status, as in the run
2026-11-11_04-19-58 skill-case-e2e-outcome-external debug_result.json).
No tenant is touched.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_run", HERE / "check_expense_runnable_run.py")
check_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_run)

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


def test_pascal_cased_rows_are_read_too() -> None:
    data = {
        "FinalStatus": "Completed",
        "ElementExecutions": [
            {"ElementId": e, "ElementType": t, "Status": s} for e, t, s in happy_rows()
        ],
    }
    assert len(check_run.check_path(PLAN, data)) == 5
