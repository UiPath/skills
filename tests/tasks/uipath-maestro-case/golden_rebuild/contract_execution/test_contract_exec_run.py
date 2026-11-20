"""check_contract_exec_run: the opening path of one debug run, read offline.

The plan restates the built ContractExecution opening (stage/task ids and
shapes from a real build's artifact): "Checking the request" starts
on case-entered and opens the required request check (action), the required
counterparty pull (api-workflow) and the optional clause analysis (agent);
the SLA-breach handler and "Add More Documents" do not start on entry.
Counsel review follows only after the request check, so the run parks there.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASE_ROOT = HERE.parent.parent
sys.path.insert(0, str(CASE_ROOT))
from _shared import case_run_path  # noqa: E402


def _task(task_id: str, task_type: str, name: str, rule: str, required: bool) -> list[dict]:
    return [{
        "id": task_id, "type": task_type, "displayName": name, "isRequired": required,
        "entryConditions": [{"rules": [[{"rule": rule}]]}],
    }]


PLAN = {"nodes": [
    {"id": "trigger_1", "type": "uipath.case.trigger"},
    {"id": "Stage_HXaQD2", "type": "case-management:Stage", "data": {
        "label": "Checking the request",
        "entryConditions": [
            {"rules": [[{"rule": "case-entered"}]]},
            {"rules": [[{"rule": "selected-stage-exited", "selectedStageIds": ["Stage_68wBiQ"]}]]},
        ],
        "tasks": [
            _task("tKhteOD4C", "action", "Validate Request Details", "current-stage-entered", True),
            _task("tMYD48OCQ", "api-workflow", "Pull Counterparty Records", "current-stage-entered", True),
            _task("tuUoi6UtD", "agent", "Analyze Draft for Unusual Clauses", "current-stage-entered", False),
            _task("tBD9CpeAy", "action", "Add More Documents", "adhoc", False),
            _task("tePkGrFjA", "api-workflow", "Handle Checking SLA Breach", "sla-status-change", False),
        ],
    }},
    {"id": "Stage_68wBiQ", "type": "case-management:Stage", "data": {
        "label": "Counsel review",
        "entryConditions": [{"rules": [[{"rule": "selected-stage-completed",
                                         "selectedStageIds": ["Stage_HXaQD2"]}]]}],
        "tasks": [_task("t69vDEQRQ", "api-workflow", "Notify Assigned Counsel", "runs-sequentially", True)],
    }},
]}
PARKED = [
    {"elementId": "trigger_1", "status": "Completed"},
    {"elementId": "Stage_HXaQD2", "status": "InProgress"},
    {"elementId": "tMYD48OCQ", "status": "Completed"},
    {"elementId": "tKhteOD4C", "status": "InProgress"},
]


def test_the_plan_names_the_opening_path() -> None:
    path = case_run_path.opening_path(PLAN)
    assert [t["displayName"] for _, t in path["automated"]] == ["Pull Counterparty Records"]
    assert [t["displayName"] for _, t in path["human"]] == ["Validate Request Details"]
    # The request check holds the stage open, so the run is not expected to reach counsel.
    assert path["next"] == []


def test_a_run_parked_at_the_request_check_passes() -> None:
    path = case_run_path.opening_path(PLAN)
    assert case_run_path.path_failures(path, {"executions": PARKED}) == []
    assert case_run_path.path_reached(path, PARKED)


def test_the_optional_clause_analysis_may_fail() -> None:
    """Debug starts with no draft attached, so the optional agent can fault."""
    path = case_run_path.opening_path(PLAN)
    rows = PARKED + [{"elementId": "tuUoi6UtD", "status": "Faulted"}]
    assert case_run_path.path_failures(path, {"executions": rows}) == []


def test_a_failed_counterparty_pull_fails() -> None:
    path = case_run_path.opening_path(PLAN)
    rows = [r for r in PARKED if r["elementId"] != "tMYD48OCQ"] + [
        {"elementId": "tMYD48OCQ", "status": "Faulted"}
    ]
    problems = case_run_path.path_failures(path, {"executions": rows})
    assert any("api-workflow task 'Pull Counterparty Records'" in p for p in problems)
    assert any("required elements failed" in p for p in problems)


def test_a_request_check_that_never_opened_fails() -> None:
    path = case_run_path.opening_path(PLAN)
    rows = [r for r in PARKED if r["elementId"] != "tKhteOD4C"]
    assert case_run_path.path_failures(path, {"executions": rows}) == [
        "human task 'Validate Request Details' in 'Checking the request' was never opened"
    ]
