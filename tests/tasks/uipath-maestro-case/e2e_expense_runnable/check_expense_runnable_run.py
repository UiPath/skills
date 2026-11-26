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

A stage ran to Completed when its own execution says so. Automation Suite 2.2610
leaves a stage's execution ``InProgress`` after the stage, and the case, have
finished, so there the run says it instead: the run is ``Completed``, the
stage's execution is ``InProgress``, and every task the design document requires
in the stage completed. Which tasks are required is read from the design
document (``SDD_REQUIRED_TASKS``): the plan under grading cannot mark one
optional, neither to skip it nor to excuse its ``Cancelled`` execution. No
other state is read this way: a stage that never started, or that ended
Terminated, did not run to its end.

The run's status is the CLI's when it reports the run's end. When the CLI
stopped short of it, the instance's own status is read on every poll, before
the stages: a stage execution left open cannot say the run ended, and one that
shows Completed cannot say the run was not stopped. The executions graded are
then read after that end. A run that ended any other way than Completed
(Stopped and Suspended included) fails before its stages are read. So does a
run whose status could not be read: an unread status is not Running.

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
from case_run import TERMINAL, instance_executions, instance_status  # noqa: E402  (_setup/, on the path once case_run_path is imported)

EXPECTED_CASEPLAN = os.path.join(
    "ExpenseReimbursementRunnable", "ExpenseReimbursementRunnable", "caseplan.json"
)
HAPPY_PATH = ("Submission", "Manager Approval", "Finance Approval", "Payment", "Approved")
# The tasks fixtures/sdd.md marks `Required: Yes` in each happy-path stage.
SDD_REQUIRED_TASKS = {
    "Submission": ("Validate Expense Data",),
    "Manager Approval": ("Send Approval Request",),
    "Finance Approval": ("Policy Compliance Check", "Budget & GL Reconciliation"),
    "Payment": ("Process Reimbursement", "Payment Confirmation"),
    "Approved": ("Send Approval Confirmation", "Update GL Records"),
}
NOT_ON_PATH = ("Rejected", "Withdrawn")
DONE = {"completed", "successful"}
DEBUG_TIMEOUT_S = 720
WAIT_BUDGET_S = 900
FINAL_STAGE = "Approved"
# Element states that mean the element never started.
NOT_STARTED = {"", "notstarted", "pending", "skipped"}
# The state Automation Suite 2.2610 leaves a stage's execution in after the stage ended.
LEFT_OPEN = {"inprogress"}
FAILED = re.compile(r"fail|fault|error|cancel", re.IGNORECASE)
FAILED_ANY = re.compile(r"fail|fault|error", re.IGNORECASE)
# How a run ends without completing. Suspended is the CLI's word for a debug run
# that stopped short (its FAULTED_DEBUG_STATUSES); case_run.TERMINAL lacks it.
ENDED_WITHOUT_COMPLETING = (TERMINAL - DONE) | {"suspended"}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def optional_ids(plan: dict) -> set[str]:
    """Ids of tasks the plan marks not required; one may end Cancelled (a timer that never fires).

    A task the design document requires is never optional, whatever the plan marks it.
    """
    sdd_required = {_norm(task) for tasks in SDD_REQUIRED_TASKS.values() for task in tasks}
    return {
        str(task.get("id"))
        for node in plan.get("nodes") or []
        for lane in (node.get("data") or {}).get("tasks") or []
        for task in (lane if isinstance(lane, list) else [lane])
        if isinstance(task, dict) and task.get("isRequired") is False
        and _norm(str(task.get("displayName") or "")) not in sdd_required
    }


def element_failed(execution: dict, optional: set[str]) -> bool:
    status = str(_get_ci(execution, "status", "Status") or "")
    if FAILED_ANY.search(status):
        return True
    element = str(_get_ci(execution, "elementId", "ElementId") or "")
    return element not in optional and bool(FAILED.search(status))


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def statuses_by_element(payload: dict) -> dict[str, list[str]]:
    """Element id -> the statuses its executions reported."""
    by_id: dict[str, list[str]] = {}
    for execution in _get_ci(payload, "elementExecutions", "ElementExecutions") or []:
        if isinstance(execution, dict):
            element = str(_get_ci(execution, "elementId", "ElementId") or "")
            by_id.setdefault(element, []).append(
                str(_get_ci(execution, "status", "Status") or "")
            )
    return by_id


def _label(stage: dict) -> str:
    return (stage.get("data") or {}).get("label") or stage.get("id")


def stage_statuses(plan: dict, by_id: dict[str, list[str]]) -> dict[str, list[str]]:
    """Stage label -> the statuses its executions reported (empty when it never ran)."""
    return {
        _label(stage): by_id.get(stage.get("id"), [])
        for stage in find_stages(plan, include_exception=True)
    }


def _done(statuses: list[str]) -> bool:
    return any(status.lower() in DONE for status in statuses)


def _left_open(statuses: list[str]) -> bool:
    """Every execution of the stage is in the open state; one that ended otherwise is the stage's answer."""
    return bool(statuses) and all(status.lower() in LEFT_OPEN for status in statuses)


def unfinished_required_tasks(plan: dict, by_id: dict[str, list[str]], name: str, label: str) -> list[str]:
    """The tasks the design document requires in the happy-path stage ``name`` that did not complete.

    The plan's own ``isRequired`` is not read: a plan that marks a required task
    optional must not pass on its own flag. A required task the plan's stage
    ``label`` lacks counts as not completed.
    """
    ids = {
        _norm(str(task.get("displayName") or "")): str(task.get("id"))
        for stage in find_stages(plan, include_exception=True)
        if _label(stage) == label
        for lane in (stage.get("data") or {}).get("tasks") or []
        for task in (lane if isinstance(lane, list) else [lane])
        if isinstance(task, dict)
    }
    return [
        task for task in SDD_REQUIRED_TASKS[name]
        if not _done(by_id.get(ids.get(_norm(task), ""), []))
    ]


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

    by_id = statuses_by_element(payload)
    statuses = stage_statuses(plan, by_id)
    run_completed = str(_get_ci(payload, "finalStatus", "FinalStatus") or "").lower() in DONE
    happy = []
    for name in HAPPY_PATH:
        label = _stage(statuses, name)
        if not _done(statuses[label]):
            # Only an execution left InProgress is read from the run: a
            # completed run in which the tasks the design requires in the stage
            # completed ran it to its end. Any other state stands as the
            # stage's own answer.
            unfinished = unfinished_required_tasks(plan, by_id, name, label)
            if not (run_completed and _left_open(statuses[label]) and not unfinished):
                _fail(
                    f"happy-path stage {label!r} did not complete in the run "
                    f"(statuses {statuses[label] or 'none: never entered'}"
                    + (f"; required tasks not completed: {unfinished}" if unfinished else "")
                    + ")"
                )
        happy.append(label)
    for name in NOT_ON_PATH:
        label = _stage(statuses, name)
        ran = [status for status in statuses[label] if status.lower() not in NOT_STARTED]
        if ran:
            _fail(f"stage {label!r} ran on the approved path (statuses {ran})")
    return happy


def _run_ended(plan: dict, run: dict):
    """The end of the wait: the instance's own end, a failed element, or the final stage Completed.

    The instance's status is read first, on every poll, unless the CLI already
    reported the run's end. A tenant that leaves stage executions open never
    shows the final stage Completed, and a final stage that shows Completed
    does not say the run was not stopped. Once the instance has ended, the wait
    stops and ``read_ended_run`` reads the finished run.

    A status read that fails returns nothing, which is not Running: the final
    stage does not end the wait on that poll, so the next poll reads it again.
    ``run["instance_status"]`` keeps the last read for ``status_unknown``.
    """

    def ended(executions: list[dict]) -> bool:
        status_known = True
        if run["status"].lower() not in TERMINAL:
            status = run["instance_status"] = instance_status(run["instance_id"])
            if status.lower() in TERMINAL or not_completed(status):
                run["ended_as"] = status
                return True
            status_known = bool(status)
        optional = optional_ids(plan)
        if any(element_failed(e, optional) for e in executions if isinstance(e, dict)):
            return True
        statuses = stage_statuses(plan, statuses_by_element({"elementExecutions": executions}))
        return status_known and _done(statuses[_stage(statuses, FINAL_STAGE)])

    return ended


def read_ended_run(run: dict) -> dict:
    """The instance ended while it was followed: take its status and read the finished run's executions.

    The executions in hand were read before the status that showed the end, so
    a task that completed in between still looks open in them. A read that
    returns nothing fails the check: the rows in hand are not the finished run's.
    """
    status = run.pop("ended_as", None)
    if not status:
        return run
    run["status"] = status
    if not_completed(status):
        return run
    rows = instance_executions(run["instance_id"])
    if not rows:
        _fail(f"the instance ended {status}, but its element executions could not be read, so the run cannot be graded")
    run["executions"] = rows
    return run


def status_unknown(run: dict) -> bool:
    """The CLI stopped before the run's end and the instance's status could not be read on the last poll."""
    return run["status"].lower() not in TERMINAL and not run.get("instance_status")


def not_completed(status: str) -> bool:
    """The run ended, or failed, without completing: Stopped and Suspended count, though no element failed."""
    return bool(FAILED.search(status)) or status.lower() in ENDED_WITHOUT_COMPLETING


def main() -> None:
    plan = read_caseplan(existing_caseplan(EXPECTED_CASEPLAN))
    run = debug_case(timeout=DEBUG_TIMEOUT_S)
    run = read_ended_run(wait_for(run, _run_ended(plan, run), budget=WAIT_BUDGET_S))
    if not_completed(run["status"]):
        _fail(f"case did not complete (finalStatus={run['status']})")
    if status_unknown(run):
        _fail(
            f"the CLI stopped before the run's end and the status of instance {run['instance_id']} "
            "could not be read, so the run cannot be graded: its stages cannot say it was not stopped"
        )
    payload = {"finalStatus": run["status"], "elementExecutions": run["executions"]}
    happy = check_path(plan, payload)
    print(
        "OK: the Approved stage completed through "
        + " -> ".join(happy)
        + "; Rejected and Withdrawn did not run"
    )


if __name__ == "__main__":
    main()
