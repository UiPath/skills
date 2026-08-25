#!/usr/bin/env python3
"""T1 — notify-only: a breach the source only wants an email for mints no stage and no task."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.sla_response_check import (  # noqa: E402
    assert_has_recipient,
    assert_no_any_sentinel,
    assert_stage_count,
    escalations_of,
    fail,
    label_of,
    read_plan,
    sla_status_change_anywhere,
    stage_by_label,
    tasks_of,
)


def main() -> None:
    plan = read_plan()

    # The escalation the source asked for, on Review's OWN SLA, with a real recipient.
    review = stage_by_label(plan, "Review")
    breached = escalations_of(review, trigger="sla-breached")
    if not breached:
        fail(
            "Review's own slaRules carry no sla-breached escalation; the requirement was to "
            "notify the review owner when the Review SLA breaches"
        )
    for esc in breached:
        assert_has_recipient(esc, "Review breach escalation")

    # notify-only means the graph is untouched.
    graph_rules = sla_status_change_anywhere(plan)
    if graph_rules:
        fail(
            f"found {len(graph_rules)} sla-status-change rule(s) for a notify-only requirement: "
            f"{graph_rules}. Absent a stated response, at-risk and breached are notifications — "
            "never a stage entry, task, or routing change."
        )
    assert_no_any_sentinel(plan)
    assert_stage_count(plan, 3)

    review_tasks = tasks_of(review)
    if len(review_tasks) != 1:
        fail(
            f"Review should still hold exactly its 1 baseline task; found {len(review_tasks)}: "
            f"{[t.get('displayName') for t in review_tasks]}. A notify-only escalation adds no task."
        )

    labels = sorted(label_of(n) for n in plan.get("nodes") or [] if n.get("type") == "case-management:Stage")
    print(f"PASS: notify-only breach escalation on Review; stages unchanged {labels}; 0 graph responses")


if __name__ == "__main__":
    main()
