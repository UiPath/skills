#!/usr/bin/env python3
"""ExpenseReimbursementRunnable: run the case once and check the path it took.

Runs ``uip maestro case debug`` on the live tenant (``debug_case`` refreshes the
solution resources first). When the CLI stops polling before the run ends, the
instance is followed to its end, then its ``elementExecutions`` are read against
the built caseplan:

  - every happy-path stage the design names (Submission, Manager Approval,
    Finance Approval, Payment, Approved) ran to Completed, so the expense ended
    approved and paid;
  - the Rejected and Withdrawn lanes did not run;
  - no element of the run failed.

Stages are found by the names the design document gives them, not by id.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    _get_ci,
    existing_caseplan,
    find_stages,
    read_caseplan,
)
from _shared.case_run_path import debug_case, wait_for  # noqa: E402

EXPECTED_CASEPLAN = os.path.join(
    "ExpenseReimbursementRunnable", "ExpenseReimbursementRunnable", "caseplan.json"
)
HAPPY_PATH = ("Submission", "Manager Approval", "Finance Approval", "Payment", "Approved")
NOT_ON_PATH = ("Rejected", "Withdrawn")
DONE = {"completed", "successful"}
DEBUG_TIMEOUT_S = 720
WAIT_BUDGET_S = 900
FINAL_STAGE = "Approved"
# Element states that mean the element never started.
NOT_STARTED = {"", "notstarted", "pending", "skipped"}
FAILED = re.compile(r"fail|fault|error|cancel", re.IGNORECASE)
FAILED_ANY = re.compile(r"fail|fault|error", re.IGNORECASE)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def optional_ids(plan: dict) -> set[str]:
    """Ids of tasks the plan marks not required; one may end Cancelled (a timer that never fires)."""
    return {
        str(task.get("id"))
        for node in plan.get("nodes") or []
        for lane in (node.get("data") or {}).get("tasks") or []
        for task in (lane if isinstance(lane, list) else [lane])
        if isinstance(task, dict) and task.get("isRequired") is False
    }


def element_failed(execution: dict, optional: set[str]) -> bool:
    status = str(_get_ci(execution, "status", "Status") or "")
    if FAILED_ANY.search(status):
        return True
    element = str(_get_ci(execution, "elementId", "ElementId") or "")
    return element not in optional and bool(FAILED.search(status))


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def stage_statuses(plan: dict, payload: dict) -> dict[str, list[str]]:
    """Stage label -> the statuses its executions reported (empty when it never ran)."""
    by_id: dict[str, list[str]] = {}
    for execution in _get_ci(payload, "elementExecutions", "ElementExecutions") or []:
        if isinstance(execution, dict):
            element = str(_get_ci(execution, "elementId", "ElementId") or "")
            by_id.setdefault(element, []).append(
                str(_get_ci(execution, "status", "Status") or "")
            )
    return {
        (stage.get("data") or {}).get("label") or stage.get("id"): by_id.get(stage.get("id"), [])
        for stage in find_stages(plan, include_exception=True)
    }


def _stage(statuses: dict[str, list[str]], name: str) -> str | None:
    wanted = _norm(name)
    matches = [label for label in statuses if wanted in _norm(label)]
    if len(matches) != 1:
        _fail(f"expected one stage named like {name!r}; stages: {sorted(statuses)}")
    return matches[0]


def check_path(plan: dict, payload: dict) -> list[str]:
    """Return the happy-path stage labels; exit with FAIL when the run strayed."""
    failed = [
        f"{_get_ci(e, 'elementId', 'ElementId')} ({_get_ci(e, 'elementType', 'ElementType')}) "
        f"{_get_ci(e, 'status', 'Status')}"
        for e in _get_ci(payload, "elementExecutions", "ElementExecutions") or []
        if isinstance(e, dict) and element_failed(e, optional_ids(plan))
    ]
    if failed:
        _fail(f"elements failed during the run: {failed}")

    statuses = stage_statuses(plan, payload)
    happy = []
    for name in HAPPY_PATH:
        label = _stage(statuses, name)
        if not any(status.lower() in DONE for status in statuses[label]):
            _fail(
                f"happy-path stage {label!r} did not complete in the run "
                f"(statuses {statuses[label] or 'none: never entered'})"
            )
        happy.append(label)
    for name in NOT_ON_PATH:
        label = _stage(statuses, name)
        ran = [status for status in statuses[label] if status.lower() not in NOT_STARTED]
        if ran:
            _fail(f"stage {label!r} ran on the approved path (statuses {ran})")
    return happy


def _run_ended(plan: dict):
    def ended(executions: list[dict]) -> bool:
        optional = optional_ids(plan)
        if any(element_failed(e, optional) for e in executions if isinstance(e, dict)):
            return True
        statuses = stage_statuses(plan, {"elementExecutions": executions})
        return any(s.lower() in DONE for s in statuses[_stage(statuses, FINAL_STAGE)])

    return ended


def main() -> None:
    plan = read_caseplan(existing_caseplan(EXPECTED_CASEPLAN))
    run = wait_for(debug_case(timeout=DEBUG_TIMEOUT_S), _run_ended(plan), budget=WAIT_BUDGET_S)
    if FAILED.search(run["status"]):
        _fail(f"case did not complete (finalStatus={run['status']})")
    payload = {"elementExecutions": run["executions"]}
    happy = check_path(plan, payload)
    print(
        "OK: the Approved stage completed through "
        + " -> ".join(happy)
        + "; Rejected and Withdrawn did not run"
    )


if __name__ == "__main__":
    main()
