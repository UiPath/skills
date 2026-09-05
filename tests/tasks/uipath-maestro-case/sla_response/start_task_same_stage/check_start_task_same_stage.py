#!/usr/bin/env python3
"""T2 — start-task: the follow-up work lives in the breached stage, keyed off its OWN SLA.

Exactly one shape is accepted — **task entry**: the follow-up task's own `entryConditions`
carry the `sla-status-change` rule. The task fires on the SLA event itself, so the stage is
not re-entered and its other tasks do not re-run.

**Stage entry on the breached stage is rejected**, even though `uip maestro case validate`
accepts it (verified on uip 1.198.0-preview.102). Re-entering the stage restarts every task
in it whose `shouldRunOnlyOnce` is `false` — the default for every task type — so a breach
meant to add one manager check silently re-runs the whole stage. See
`skills/uipath-maestro-case/references/sla-response-shapes.md` section 5, defect 4.

The rule must reference **Review's own** SLA and be a breach rule (`slaId`, no
`escalationId`), and the follow-up task must be an `action` task in Review with a working
activation. Also rejected is the `enter-stage` answer: putting the work in a separate lane.
"""

import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-maestro-case")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.sla_response_check import (  # noqa: E402
    assert_breach_shape,
    assert_no_any_sentinel,
    assert_sla_resolves,
    assert_stage_count,
    fail,
    iter_sla_status_change,
    iter_task_sla_status_change,
    label_of,
    read_plan,
    stage_by_label,
    tasks_of,
)

BASELINE_TASK = "Hold For 1 Hour"


def main() -> None:
    plan = read_plan()
    assert_no_any_sentinel(plan)

    # No separate escalation lane: the response is local to Review.
    assert_stage_count(plan, 3)

    task_hits = list(iter_task_sla_status_change(plan))
    stage_hits = list(iter_sla_status_change(plan))
    if not task_hits and not stage_hits:
        fail(
            "no sla-status-change rule anywhere; the Review breach was supposed to start a "
            "follow-up task inside Review, with the rule on that task's own entry condition"
        )
    if len(task_hits) + len(stage_hits) > 1:
        where = [f"task:{t.get('displayName')}" for _n, t, _c, _r in task_hits]
        where += [f"stage:{label_of(n)}" for n, _c, _r in stage_hits]
        fail(f"expected exactly 1 sla-status-change rule, found {len(where)}: {where}")

    if not task_hits:
        node, cond, rule = stage_hits[0]
        if label_of(node) != "Review":
            fail(
                f"the sla-status-change entry sits on stage {label_of(node)!r}. A start-task "
                "response keeps the work in the breached stage (Review) — a separate lane is "
                "the enter-stage response, which this requirement did not ask for."
            )
        fail(
            "the sla-status-change rule is a Review STAGE-entry condition "
            f"({cond.get('displayName')!r}). A start-task response belongs on the follow-up "
            "TASK's own entryConditions. validate accepts stage re-entry, but re-entering "
            "Review restarts every task whose shouldRunOnlyOnce is false (the default), not "
            "just the manager check — see references/sla-response-shapes.md section 5, defect 4."
        )

    node, task, _cond, rule = task_hits[0]
    where = f"task {task.get('displayName')!r} entry condition"
    if label_of(node) != "Review":
        fail(f"the follow-up task sits in stage {label_of(node)!r}; it belongs in Review")
    shape = f"task-entry on {task.get('displayName')!r}"
    followups = [task]

    assert_sla_resolves(plan, rule, where, owner="Review")
    assert_breach_shape(rule, where)

    review_tasks = tasks_of(stage_by_label(plan, "Review"))
    added = [t for t in review_tasks if t.get("displayName") != BASELINE_TASK]
    if not added:
        fail(f"no follow-up task added to Review; tasks present: {[t.get('displayName') for t in review_tasks]}")
    actions = [t for t in added if t.get("type") == "action"]
    if not actions:
        fail(
            "the manager check should be an `action` (human) task; got "
            f"{[(t.get('displayName'), t.get('type')) for t in added]}"
        )
    for action in actions:
        # A condition carrying no rules is as unstartable as no condition at all.
        if not any((c.get("rules") or []) for c in (action.get("entryConditions") or [])):
            fail(
                f"task {action.get('displayName')!r} has no usable entry condition — it can never "
                "start. validate accepts an empty array, a missing key, and a condition with an "
                "empty rules list, so it is on the author."
            )
    if followups and not any(t.get("type") == "action" for t in followups):
        fail(f"the sla-status-change rule is not wired to an action task; found {followups}")

    print(
        f"PASS: {shape} — breach rule on Review's own SLA ({rule['slaId']}, no escalationId); "
        f"follow-up action task {[t.get('displayName') for t in actions]} in Review; 3 stages"
    )


if __name__ == "__main__":
    main()
