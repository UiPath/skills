#!/usr/bin/env python3
"""Diagnose → fix a pre-broken caseplan.json: root-cause grader.

The fixture stages a LinearThreeStages case (Intake → Review → Decision)
with two deliberate defects that `uip maestro case validate` reports:

  A. Decision's stage-entry condition references a non-existent stage
     (`selectedStageId: "Stage_Ghost404"`) — Decision is unreachable / orphaned
     and the reference dangles.
  B. Intake's task carries `type: "wait-for-event"` — not one of the 9 closed
     task-type enum values (Critical Rule 16).

This grader confirms the agent fixed the ACTUAL root causes rather than
deleting stages/tasks to silence the validator:

  1. Task shape is well-formed (2D Task[][] lanes).
  2. The three primary stages (Intake, Review, Decision) all still exist — the
     agent didn't drop a stage to make errors disappear.
  3. Bug B fixed: no `wait-for-event` anywhere and every task `type` is one of
     the 9 closed enum values.
  4. Bug A fixed: the `Stage_Ghost404` dangling reference is gone, every
     stage-entry `selectedStageId` resolves to an existing node, and Decision
     is reachable from Intake through condition-derived transitions.
  5. The manual trigger and the case-exit rule are preserved.

Validation-passes is graded separately by a `run_command` on `uip maestro case
validate` in the task YAML; this script asserts the fixes are the right ones.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import (  # noqa: E402
    assert_tasks_nested,
    find_stages,
    find_transitions,
    find_triggers,
    get_case_exit_conditions,
    iter_tasks,
    read_caseplan,
)

# Critical Rule 16 — the closed task-type enum (schema-kebab).
VALID_TASK_TYPES = {
    "process",
    "agent",
    "rpa",
    "action",
    "api-workflow",
    "case-management",
    "execute-connector-activity",
    "wait-for-connector",
    "wait-for-timer",
}

PRIMARY_STAGES = ["Intake", "Review", "Decision"]
GHOST_ID = "Stage_Ghost404"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _label(node: dict) -> str:
    return (node.get("data") or {}).get("label") or ""


def _find_stage_by_name(stages: list[dict], target: str) -> dict | None:
    tnorm = _norm(target)
    for s in stages:
        if tnorm in _norm(_label(s)):
            return s
    return None


def _has_path(plan: dict, src_id: str, dst_id: str, max_hops: int = 8) -> bool:
    if src_id == dst_id:
        return True
    frontier = {src_id}
    seen = {src_id}
    for _ in range(max_hops):
        nxt = set()
        for node_id in frontier:
            for tr in find_transitions(plan, source=node_id):
                t = tr.get("target")
                if t == dst_id:
                    return True
                if t and t not in seen:
                    seen.add(t)
                    nxt.add(t)
        if not nxt:
            return False
        frontier = nxt
    return False


def _fail(msg: str):
    sys.exit(f"FAIL: {msg}")


def main():
    plan = read_caseplan()
    assert_tasks_nested(plan)

    # 2. All three primary stages preserved.
    stages = find_stages(plan, include_exception=True)
    labels = [_label(s) for s in stages]
    primary = {}
    missing = []
    for name in PRIMARY_STAGES:
        node = _find_stage_by_name(stages, name)
        if node:
            primary[name] = node
        else:
            missing.append(name)
    if missing:
        _fail(
            f"missing stage(s) {missing} — the fix must repair the defects, not "
            f"delete stages to silence the validator. Stages present: {labels}"
        )

    # 3. Bug B — no invalid task types remain.
    node_ids = {n.get("id") for n in plan.get("nodes") or []}
    bad_types = sorted(
        {t.get("type") for t in iter_tasks(plan) if t.get("type") not in VALID_TASK_TYPES}
    )
    if bad_types:
        _fail(
            f"task type(s) {bad_types} are not in the closed 9-value enum "
            f"(Rule 16); 'wait-for-event' was the planted defect and must be "
            f"replaced with a valid type"
        )

    # 4. Bug A — dangling reference gone, all selectedStageId resolve, Decision reachable.
    if GHOST_ID in repr(plan):
        _fail(
            f"the dangling reference {GHOST_ID!r} is still present — Decision's "
            f"entry condition must be repointed at a real stage"
        )
    for stage in stages:
        for cond in (stage.get("data") or {}).get("entryConditions") or []:
            for group in cond.get("rules") or []:
                for rule in group or []:
                    sid = (rule or {}).get("selectedStageId")
                    if sid and sid not in node_ids:
                        _fail(
                            f"stage {_label(stage)!r} entry condition references "
                            f"non-existent stage id {sid!r}"
                        )
    if not _has_path(plan, primary["Intake"]["id"], primary["Decision"]["id"]):
        _fail(
            "Decision is not reachable from Intake through condition-derived "
            "transitions — the rewired entry condition must chain Decision back "
            "into the Intake→Review→Decision path"
        )

    # 5. Trigger + case-exit preserved.
    if not find_triggers(plan):
        _fail("manual trigger node was removed; it must be preserved")
    if not get_case_exit_conditions(plan):
        _fail("metadata.caseExitRules was removed; it must be preserved")

    task_count = sum(1 for _ in iter_tasks(plan))
    print(
        f"OK: 3 primary stages preserved ({[_label(primary[n]) for n in PRIMARY_STAGES]}); "
        f"no invalid task types; no dangling stage references; "
        f"Decision reachable from Intake; {task_count} tasks total"
    )


if __name__ == "__main__":
    main()
