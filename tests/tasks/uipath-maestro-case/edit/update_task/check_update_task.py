#!/usr/bin/env python3
"""Update-task edit check.

The starting fixture chains three stages: Intake → Review → Decision. The
Review stage runs TWO parallel wait-for-timer tasks in distinct data.tasks
lanes: "Hold For 1 Hour" (required) and "Notify Reviewer" (optional). The
agent must flip "Notify Reviewer" to required (isRequired true) in place,
leaving everything else — both tasks, the surviving properties of the edited
task, the sibling task, the stage chain — untouched. Verifies the single
property changed, the task was not otherwise rewritten or duplicated, and the
edited case launches (an in-place update, not a rebuild).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    _get_ci,
    find_caseplan,
    find_node_by_label,
    find_stages,
    find_transitions,
    read_caseplan,
    start_debug,
)


def _stage_tasks(node):
    lanes = (node.get("data") or {}).get("tasks") or []
    return [t for lane in lanes for t in (lane or [])]


def _entry_rule(task):
    conds = task.get("entryConditions") or []
    if not conds:
        return None
    groups = conds[0].get("rules") or []
    if groups and groups[0]:
        return groups[0][0]
    return None


def main():
    caseplan_path = find_caseplan()
    plan = read_caseplan(caseplan_path)

    # Stage chain must be untouched: still 3 regular stages.
    stages = find_stages(plan, include_exception=False)
    if len(stages) != 3:
        labels = [(s.get("data") or {}).get("label") for s in stages]
        sys.exit(
            f"FAIL: expected the 3 original stages (Intake, Review, Decision) "
            f"to be unchanged; got {len(stages)}: {labels}"
        )

    intake = find_node_by_label(plan, "Intake")
    review = find_node_by_label(plan, "Review")
    decision = find_node_by_label(plan, "Decision")

    # Review must still carry exactly its two tasks — no add, no remove.
    review_tasks = _stage_tasks(review)
    names = sorted(t.get("displayName") for t in review_tasks)
    if names != ["Hold For 1 Hour", "Notify Reviewer"]:
        sys.exit(
            f"FAIL: Review must still carry exactly its two tasks "
            f"('Hold For 1 Hour', 'Notify Reviewer'); got {names} — no task "
            f"should be added or removed by an in-place update"
        )

    # Both tasks must remain in DISTINCT lanes (parallel), as in the fixture.
    lanes = (review.get("data") or {}).get("tasks") or []
    if len([lane for lane in lanes if lane]) != 2:
        sys.exit(
            f"FAIL: Review's two tasks must stay in two distinct data.tasks "
            f"lanes; got lane layout {[len(lane or []) for lane in lanes]}"
        )

    notify = next(t for t in review_tasks if t.get("displayName") == "Notify Reviewer")
    hold = next(t for t in review_tasks if t.get("displayName") == "Hold For 1 Hour")

    # The one intended change: "Notify Reviewer" is now required.
    if notify.get("isRequired") is not True:
        sys.exit(
            f"FAIL: 'Notify Reviewer' must be flipped to required "
            f"(isRequired=true); got isRequired={notify.get('isRequired')!r}"
        )

    # "Notify Reviewer" must be otherwise unchanged: still a wait-for-timer
    # with its current-stage-entered task-entry condition.
    if notify.get("type") != "wait-for-timer":
        sys.exit(
            f"FAIL: 'Notify Reviewer' should stay a wait-for-timer task; "
            f"got type={notify.get('type')!r}"
        )
    rule = _entry_rule(notify)
    if not rule or rule.get("rule") != "current-stage-entered":
        sys.exit(
            f"FAIL: 'Notify Reviewer' task-entry rule should be "
            f"'current-stage-entered'; got {rule and rule.get('rule')!r}"
        )

    # The sibling task must be left required and unchanged — only "Notify
    # Reviewer" should have changed.
    if hold.get("isRequired") is not True:
        sys.exit(
            f"FAIL: 'Hold For 1 Hour' should stay required (isRequired=true); "
            f"got isRequired={hold.get('isRequired')!r} — only 'Notify "
            f"Reviewer' should change"
        )

    # The linear chain must be intact: Intake → Review → Decision.
    if not find_transitions(plan, source=intake["id"], target=review["id"]):
        sys.exit("FAIL: the Intake → Review transition was disturbed by the edit")
    if not find_transitions(plan, source=review["id"], target=decision["id"]):
        sys.exit("FAIL: the Review → Decision transition was disturbed by the edit")

    # e2e: the edited case must launch and run in the Studio Web debug runtime.
    # Every task is a built-in wait-for-timer (no registry resources), but the
    # case runtime suspends on wait-for-timer tasks, so the case won't
    # necessarily reach Completed in one debug pass — start_debug refreshes
    # solution resources, launches debug, and asserts it ran (tolerating a
    # non-Completed finalStatus), exactly as the sibling edit e2e checks do for
    # this same case shape.
    payload = start_debug(timeout=540)
    status = _get_ci(payload, "finalStatus", "FinalStatus", "status", "Status")

    print(
        "OK: 'Notify Reviewer' flipped to required in Review (3 stages "
        "unchanged); Review still carries both tasks in two distinct lanes; "
        "'Notify Reviewer' otherwise intact (type + current-stage-entered "
        "entry preserved); 'Hold For 1 Hour' left required and unchanged; "
        "Intake → Review → Decision chain unchanged; edited case launched in "
        f"debug runtime (status={status})"
    )


if __name__ == "__main__":
    main()
