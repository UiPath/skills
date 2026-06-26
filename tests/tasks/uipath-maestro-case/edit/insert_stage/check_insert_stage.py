#!/usr/bin/env python3
"""Insert-stage edit check.

The starting fixture chains three stages: Intake → Review → Decision. The
agent must insert a new "Approval" stage (carrying one wait-for-timer task)
between Review and Decision, rewiring the condition-driven chain so Approval
runs after Review and Decision runs after Approval. Verifies the insert
happened AND the old Review → Decision hand-off was removed (a true insert,
not an append).
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
    first_rule_of_condition,
    read_caseplan,
    start_debug,
)


def main():
    caseplan_path = find_caseplan()
    plan = read_caseplan(caseplan_path)

    stages = find_stages(plan, include_exception=False)
    if len(stages) != 4:
        labels = [(s.get("data") or {}).get("label") for s in stages]
        sys.exit(
            f"FAIL: expected 4 regular stages after inserting Approval "
            f"(Intake, Review, Approval, Decision); got {len(stages)}: {labels}"
        )

    approval = find_node_by_label(plan, "Approval")
    review = find_node_by_label(plan, "Review")
    decision = find_node_by_label(plan, "Decision")

    # Approval must carry at least one wait-for-timer task with a
    # current-stage-entered task-entry condition.
    approval_lanes = (approval.get("data") or {}).get("tasks") or []
    approval_tasks = [t for lane in approval_lanes for t in (lane or [])]
    if not approval_tasks:
        sys.exit("FAIL: Approval stage has no tasks; expected one wait-for-timer task")
    timers = [t for t in approval_tasks if t.get("type") == "wait-for-timer"]
    if not timers:
        types_seen = sorted({t.get("type", "?") for t in approval_tasks})
        sys.exit(
            f"FAIL: Approval stage has no wait-for-timer task; task types seen: {types_seen}"
        )
    timer = timers[0]
    conds = timer.get("entryConditions") or []
    rule = first_rule_of_condition(conds[0]) if conds else None
    if not rule or rule.get("rule") != "current-stage-entered":
        sys.exit(
            f"FAIL: Approval's wait-for-timer task-entry rule should be "
            f"'current-stage-entered'; got {rule and rule.get('rule')!r}"
        )

    # Reachability is condition-driven (edges retired): the chain must now run
    # Review → Approval → Decision.
    if not find_transitions(plan, source=review["id"], target=approval["id"]):
        sys.exit(
            "FAIL: no Review → Approval transition; Approval's entry condition must "
            "name Review (selected-stage-completed/-exited selectedStageId=Review)"
        )
    if not find_transitions(plan, source=approval["id"], target=decision["id"]):
        sys.exit(
            "FAIL: no Approval → Decision transition; Decision's entry condition must "
            "name Approval (selected-stage-completed/-exited selectedStageId=Approval)"
        )

    # True insert, not append: the old direct Review → Decision hand-off must
    # be gone — Decision is rewired to follow Approval.
    if find_transitions(plan, source=review["id"], target=decision["id"]):
        sys.exit(
            "FAIL: a direct Review → Decision transition still exists; Approval was "
            "appended in parallel rather than inserted into the chain. Decision's "
            "entry condition must reference Approval, not Review."
        )

    # e2e: the edited case must launch and run in the Studio Web debug runtime.
    # Every task is a built-in wait-for-timer (no registry resources), but the
    # case runtime suspends on wait-for-timer tasks, so the case won't
    # necessarily reach Completed in one debug pass — start_debug refreshes
    # solution resources, launches debug, and asserts it ran (tolerating a
    # non-Completed finalStatus), exactly as the sibling linear_three_stages
    # e2e check does for this same case shape.
    payload = start_debug(timeout=540)
    status = _get_ci(payload, "finalStatus", "FinalStatus", "status", "Status")

    print(
        "OK: Approval stage inserted between Review and Decision (4 stages total); "
        "Approval carries a wait-for-timer task ('Approval Hold') with "
        "current-stage-entered task-entry; chain rewired Review → Approval → "
        "Decision with the old Review → Decision hand-off removed; "
        f"edited case launched in debug runtime (status={status})"
    )


if __name__ == "__main__":
    main()
