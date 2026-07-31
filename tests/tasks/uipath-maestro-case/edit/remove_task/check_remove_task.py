#!/usr/bin/env python3
"""Remove-task edit check.

The starting fixture chains three stages: Intake → Review → Decision. The
Review stage runs TWO parallel wait-for-timer tasks in distinct data.tasks
lanes: "Hold For 1 Hour" (required) and "Notify Reviewer" (optional). The
agent must remove the REQUIRED "Hold For 1 Hour" task — Review's ONLY required
task — leaving Review with exactly one task ("Notify Reviewer"). Because a
required-tasks-completed exit rule needs at least one required task to stay
valid, the agent must promote the surviving "Notify Reviewer" to required
while leaving it otherwise unchanged, keeping Review's required-tasks-completed
exit condition intact. Verifies the removal happened, the survivor was promoted
to required and is otherwise intact, the exit condition still holds, the stage
chain is intact (a true delete, not a rebuild), and the edited case launches.
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
    iter_stage_exit_conditions,
    iter_tasks,
    read_caseplan,
    start_debug,
)


def _stage_tasks(node):
    lanes = (node.get("data") or {}).get("tasks") or []
    return [t for lane in lanes for t in (lane or [])]


def _has_required_tasks_completed_exit(node):
    """True when the stage keeps a marksStageComplete exit rule whose rule is
    'required-tasks-completed'."""
    for cond in iter_stage_exit_conditions(node):
        if not cond.get("marksStageComplete"):
            continue
        for group in cond.get("rules") or []:
            for rule in group or []:
                if (rule or {}).get("rule") == "required-tasks-completed":
                    return True
    return False


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

    # "Hold For 1 Hour" must be gone from the ENTIRE case, not just Review.
    if any(t.get("displayName") == "Hold For 1 Hour" for t in iter_tasks(plan)):
        sys.exit(
            "FAIL: a task named 'Hold For 1 Hour' still exists in the case; "
            "the required task must be removed entirely"
        )

    # Review must carry exactly ONE task, the surviving "Notify Reviewer".
    review_tasks = _stage_tasks(review)
    if len(review_tasks) != 1:
        names = [t.get("displayName") for t in review_tasks]
        sys.exit(
            f"FAIL: Review must carry exactly one task after removal "
            f"('Notify Reviewer'); got {len(review_tasks)}: {names}"
        )

    survivor = review_tasks[0]
    if survivor.get("displayName") != "Notify Reviewer":
        sys.exit(
            f"FAIL: the surviving Review task should be 'Notify Reviewer'; "
            f"got {survivor.get('displayName')!r} — the wrong task was removed"
        )

    # The survivor must be left intact: still a wait-for-timer with its
    # current-stage-entered task-entry condition.
    if survivor.get("type") != "wait-for-timer":
        sys.exit(
            f"FAIL: 'Notify Reviewer' should stay a wait-for-timer task; "
            f"got type={survivor.get('type')!r}"
        )
    conds = survivor.get("entryConditions") or []
    rule = None
    if conds:
        groups = conds[0].get("rules") or []
        if groups and groups[0]:
            rule = groups[0][0]
    if not rule or rule.get("rule") != "current-stage-entered":
        sys.exit(
            f"FAIL: 'Notify Reviewer' task-entry rule should be "
            f"'current-stage-entered'; got {rule and rule.get('rule')!r}"
        )

    # The survivor must be promoted to required. "Hold For 1 Hour" was Review's
    # only required task; a required-tasks-completed exit rule needs at least
    # one required task, so leaving "Notify Reviewer" optional would make the
    # stage's exit condition invalid (it could never complete / fails validate).
    if not survivor.get("isRequired"):
        sys.exit(
            "FAIL: 'Notify Reviewer' must be promoted to required "
            "(isRequired: true) so Review's required-tasks-completed exit rule "
            "still has a required task; got isRequired=false"
        )

    # Review's exit condition must still hold: the required-tasks-completed
    # marksStageComplete rule must survive the delete unrewritten. Removing the
    # only required task must NOT have torn out or weakened the exit rule.
    if not _has_required_tasks_completed_exit(review):
        sys.exit(
            "FAIL: Review's required-tasks-completed exit condition is gone or "
            "was rewritten; deleting the required task must leave the stage's "
            "marksStageComplete exit rule intact"
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
    # non-Completed finalStatus), exactly as the sibling insert_stage e2e check
    # does for this same case shape.
    payload = start_debug(timeout=540)
    status = _get_ci(payload, "finalStatus", "FinalStatus", "status", "Status")

    print(
        "OK: required 'Hold For 1 Hour' removed from Review (3 stages unchanged); "
        "Review now carries exactly one task ('Notify Reviewer') left intact "
        "(type + current-stage-entered entry preserved); Review's "
        "required-tasks-completed exit condition still holds; Intake → Review → "
        f"Decision chain unchanged; edited case launched in debug runtime "
        f"(status={status})"
    )


if __name__ == "__main__":
    main()
