#!/usr/bin/env python3
"""T5b — a case-breach oversight response the source wants to run alongside the work.

Same requirement family as T5a, one clause different: the case team keeps working while
the director oversees. Two honest shapes exist, and either passes:

  task  — the skill's parallel-oversight shape (Rule 21, sla-response-shapes.md §4): one
          non-required task whose own entry is sla-status-change on the root SLA, and no
          new stage. Runtime (debug instance 583c4102, 2026-10-06): a root-SLA breach
          during Intake started such a task in Intake AND one in not-yet-entered Decision,
          cancelled nothing, and the case completed all three stages — so it runs
          alongside wherever it sits.
  lane  — what the prompt literally names: a secondary, non-required stage entered on the
          breach. Every secondary-stage entry interrupts (debug instance 72162d9b: the
          breach exited the active stage and cancelled its task), so the entry must carry
          isInterrupting True; the judge then requires the reply to disclose the pause.

The shape built is printed as `SHAPE=task|lane` for the judge to read.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import is_non_required  # noqa: E402
from _shared.sla_response_check import (  # noqa: E402
    iter_task_sla_status_change,
    assert_breach_shape,
    assert_no_any_sentinel,
    assert_sla_resolves,
    assert_stage_count,
    fail,
    is_secondary,
    iter_sla_status_change,
    label_of,
    read_plan,
)


def check_task_shape(plan: dict) -> None:
    assert_stage_count(plan, 3)
    hits = list(iter_task_sla_status_change(plan))
    if len(hits) != 1:
        where = [(label_of(n), t.get("displayName")) for n, t, _, _ in hits]
        fail(f"expected exactly 1 task-entry sla-status-change rule, found {len(hits)}: {where}")
    stage, task, cond, rule = hits[0]
    if not is_non_required(task):
        fail(
            f"oversight task {task.get('displayName')!r} has isRequired={task.get('isRequired')!r}; "
            "a case must finish normally without the director's oversight"
        )
    where = f"task {task.get('displayName')!r} entry condition {cond.get('displayName')!r}"
    assert_sla_resolves(plan, rule, where, owner="root")
    assert_breach_shape(rule, where)
    print(
        f"PASS SHAPE=task: oversight task {task.get('displayName')!r} in {label_of(stage)!r} "
        f"starts on root SLA {rule['slaId']} breach (no escalationId), isRequired False; no new stage"
    )


def check_lane_shape(plan: dict) -> None:
    assert_stage_count(plan, 4)
    hits = list(iter_sla_status_change(plan))
    if len(hits) != 1:
        where = [(label_of(n), c.get("displayName")) for n, c, _ in hits]
        fail(f"expected exactly 1 sla-status-change stage-entry rule, found {len(hits)}: {where}")
    lane, cond, rule = hits[0]
    if label_of(lane) in {"Intake", "Review", "Decision"}:
        fail(f"the oversight entry landed on baseline stage {label_of(lane)!r}")
    if not is_secondary(lane):
        fail(
            f"lane {label_of(lane)!r} has stageType={(lane['data'].get('stageType'))!r}; a "
            "SLA oversight lane stays `secondary` — promoting it to a regular stage would make "
            "it required for case completion"
        )
    if not is_non_required(lane["data"]):
        fail(
            f"lane {label_of(lane)!r} has isRequired={lane['data'].get('isRequired')!r}; an "
            "oversight lane must stay out of the required-stages-completed set"
        )
    where = f"{label_of(lane)} entry condition {cond.get('displayName')!r}"
    assert_sla_resolves(plan, rule, where, owner="root")
    assert_breach_shape(rule, where)
    if cond.get("isInterrupting") is not True:
        fail(
            f"{where} has isInterrupting={cond.get('isInterrupting')!r}; a secondary-stage entry "
            "always interrupts at runtime whatever the flag says, so the only honest value is True"
        )
    print(
        f"PASS SHAPE=lane: oversight lane {label_of(lane)!r} on root SLA {rule['slaId']} "
        "(no escalationId), isInterrupting True; secondary + isRequired False"
    )


def main() -> None:
    plan = read_plan()
    assert_no_any_sentinel(plan)
    stage_hits = list(iter_sla_status_change(plan))
    task_hits = list(iter_task_sla_status_change(plan))
    if stage_hits and task_hits:
        fail("both a stage-entry and a task-entry sla-status-change rule: pick one oversight shape")
    if stage_hits:
        check_lane_shape(plan)
    elif task_hits:
        check_task_shape(plan)
    else:
        fail("no sla-status-change rule anywhere: the breach starts no oversight")


if __name__ == "__main__":
    main()
