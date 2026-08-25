#!/usr/bin/env python3
"""Remove-stage edit check.

The starting fixture chains three stages linearly: Intake → Review → Decision,
wired through condition-driven stage-entry rules. The agent must delete the
MIDDLE "Review" stage (its node and all of its tasks) and rewire Decision to
enter after Intake, leaving no reference to the removed stage anywhere.
Verifies the whole stage is gone (not just relabeled), the chain was rejoined
into a direct Intake → Decision hand-off with no dangling condition reference,
Intake was left intact, and the edited case still launches (a true delete-and-
reconnect, not a rebuild). Distinct from remove_task, which drops a leaf task.
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
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    iter_tasks,
    read_caseplan,
    start_debug,
)


def _stage_tasks(node):
    lanes = (node.get("data") or {}).get("tasks") or []
    return [t for lane in lanes for t in (lane or [])]


def _dangling_stage_refs(plan):
    """Return (label, referenced_id) for every condition that points at a
    stage id no node in the plan carries — i.e. a leftover reference to a
    deleted stage."""
    node_ids = {n.get("id") for n in plan.get("nodes") or []}
    dangling = []
    for node in plan.get("nodes") or []:
        if "Stage" not in (node.get("type") or ""):
            continue
        label = (node.get("data") or {}).get("label") or node.get("id")
        for cond in iter_stage_entry_conditions(node):
            for group in cond.get("rules") or []:
                for rule in group or []:
                    sid = (rule or {}).get("selectedStageId")
                    if sid and sid not in node_ids:
                        dangling.append((label, sid))
        for cond in iter_stage_exit_conditions(node):
            dst = cond.get("exitToStageId")
            if dst and dst not in node_ids:
                dangling.append((label, dst))
    return dangling


def main():
    caseplan_path = find_caseplan()
    plan = read_caseplan(caseplan_path)

    # Exactly two regular stages must remain: Intake and Decision.
    stages = find_stages(plan, include_exception=False)
    labels = sorted((s.get("data") or {}).get("label") for s in stages)
    if labels != ["Decision", "Intake"]:
        sys.exit(
            f"FAIL: after removing Review the case must carry exactly the two "
            f"stages Intake and Decision; got {labels}"
        )

    # The Review stage and its tasks must be gone from the ENTIRE case, not
    # merely relabeled — no residual "Review" node, and its two tasks removed.
    if any((s.get("data") or {}).get("label") == "Review" for s in stages):
        sys.exit("FAIL: a stage still labeled 'Review' exists; the stage must be removed")
    leftover_tasks = [
        t.get("displayName")
        for t in iter_tasks(plan)
        if t.get("displayName") in {"Hold For 1 Hour", "Notify Reviewer"}
    ]
    if leftover_tasks:
        sys.exit(
            f"FAIL: tasks from the removed Review stage still exist in the case: "
            f"{leftover_tasks}; deleting the stage must delete its tasks too"
        )

    # No condition may point at a stage id that no longer exists (a leftover
    # reference to the deleted Review stage).
    dangling = _dangling_stage_refs(plan)
    if dangling:
        sys.exit(
            f"FAIL: dangling stage reference(s) to a deleted stage remain in "
            f"conditions (stage → referenced id): {dangling}; rewire the chain "
            f"so no condition references the removed Review stage"
        )

    intake = find_node_by_label(plan, "Intake")
    decision = find_node_by_label(plan, "Decision")

    # The chain must be rejoined: Decision now enters after Intake completes.
    if not find_transitions(plan, source=intake["id"], target=decision["id"]):
        sys.exit(
            "FAIL: no Intake → Decision transition; Decision's stage-entry "
            "condition must be rewired to reference the Intake stage after "
            "Review's removal"
        )

    # Intake must be left intact: still carries its task and its case-entered
    # entry rule.
    intake_tasks = _stage_tasks(intake)
    if not intake_tasks:
        sys.exit("FAIL: Intake lost its task(s); the edit must leave Intake unchanged")
    intake_rule = None
    conds = list(iter_stage_entry_conditions(intake))
    if conds:
        groups = conds[0].get("rules") or []
        if groups and groups[0]:
            intake_rule = groups[0][0]
    if not intake_rule or intake_rule.get("rule") != "case-entered":
        sys.exit(
            f"FAIL: Intake's case-entered entry rule was disturbed; got "
            f"{intake_rule and intake_rule.get('rule')!r}"
        )

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
        "OK: Review stage removed (node + tasks gone from the whole case); "
        "exactly two stages remain (Intake, Decision); no dangling condition "
        "reference to the deleted stage; chain rejoined into a direct Intake → "
        "Decision hand-off; Intake left intact (task + case-entered entry "
        f"preserved); edited case launched in debug runtime (status={status})"
    )


if __name__ == "__main__":
    main()
