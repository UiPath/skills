#!/usr/bin/env python3
"""T2 — start-task: the breached stage carries the entry on its OWN SLA, non-interrupting."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.sla_response_check import (  # noqa: E402
    assert_breach_shape,
    assert_interrupting,
    assert_no_any_sentinel,
    assert_sla_resolves,
    assert_stage_count,
    fail,
    iter_sla_status_change,
    label_of,
    read_plan,
    stage_by_label,
    tasks_of,
)


def main() -> None:
    plan = read_plan()
    assert_no_any_sentinel(plan)

    hits = list(iter_sla_status_change(plan))
    if not hits:
        fail(
            "no sla-status-change entry condition anywhere; the Review breach was supposed to "
            "start a follow-up task inside Review"
        )
    if len(hits) > 1:
        where = [(label_of(n), c.get("displayName")) for n, c, _ in hits]
        fail(f"expected exactly 1 sla-status-change entry rule, found {len(hits)}: {where}")

    node, cond, rule = hits[0]
    if label_of(node) != "Review":
        fail(
            f"the sla-status-change entry sits on stage {label_of(node)!r}; a start-task response "
            "belongs on the breached stage itself (Review)"
        )

    where = f"Review entry condition {cond.get('displayName')!r}"
    assert_sla_resolves(plan, rule, where, owner="Review")
    assert_breach_shape(rule, where)
    assert_interrupting(cond, False, where)

    # No separate escalation lane was minted.
    assert_stage_count(plan, 3)

    # The follow-up task lives in Review. Activation semantics are deliberately not
    # asserted: the skill does not yet specify the task-entry rule for a re-entered
    # stage, so any non-empty entry condition is accepted here.
    review_tasks = tasks_of(stage_by_label(plan, "Review"))
    added = [t for t in review_tasks if t.get("displayName") != "Hold For 1 Hour"]
    if not added:
        names = [t.get("displayName") for t in review_tasks]
        fail(f"no follow-up task added to Review; tasks present: {names}")
    actions = [t for t in added if t.get("type") == "action"]
    if not actions:
        got = [(t.get("displayName"), t.get("type")) for t in added]
        fail(f"the manager check should be an `action` (human) task; got {got}")
    for task in actions:
        if not (task.get("entryConditions") or []):
            fail(f"task {task.get('displayName')!r} has no entry condition — it can never start")

    print(
        f"PASS: Review carries a non-interrupting breach entry on its own SLA "
        f"({rule['slaId']}, no escalationId); follow-up action task "
        f"{[t.get('displayName') for t in actions]} in Review; 3 stages"
    )


if __name__ == "__main__":
    main()
