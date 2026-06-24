#!/usr/bin/env python3
"""BranchingExit: Triage wide fan-outs to 3 branches via selected-tasks-completed
(Approved/Rejected, marks-complete:false) + required-tasks-completed (Pending,
marks-complete:true) exits; every stage carries a process skeleton placeholder."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_count,
    find_node_by_label,
    find_stages,
    first_rule_of_condition,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    read_caseplan,
    task_is_skeleton,
)


def _stage_tasks(stage: dict) -> list[dict]:
    """Flatten a stage's data.tasks lanes into a list of task dicts."""
    lanes = (stage.get("data") or {}).get("tasks") or []
    return [t for lane in lanes for t in (lane or []) if isinstance(t, dict)]


def _stage_task_by_label(stage: dict, label: str) -> dict:
    for task in _stage_tasks(stage):
        if task.get("displayName") == label or task.get("label") == label:
            return task
    saw = [t.get("displayName") or t.get("label") for t in _stage_tasks(stage)]
    sys.exit(
        f"FAIL: task with displayName/label={label!r} not found in stage "
        f"{(stage.get('data') or {}).get('label')!r}; saw {saw}"
    )


def main():
    plan = read_caseplan()

    stages = find_stages(plan, include_exception=False)
    assert_count(len(stages), 4, "regular stage(s)")

    triage = find_node_by_label(plan, "Triage")
    approved = find_node_by_label(plan, "Approved Path")
    rejected = find_node_by_label(plan, "Rejected Path")
    pending = find_node_by_label(plan, "Pending Path")

    # Reachability is condition-driven (edges retired): Triage's three stage-exit
    # conditions route to the three branches via exitToStageId (asserted below),
    # and each exit rule's conditionExpression on vars.decision discriminates the
    # branch. There are no edges, no edge labels, and no edge handles to check.
    exit_conds = list(iter_stage_exit_conditions(triage))
    if len(exit_conds) < 3:
        sys.exit(
            f"FAIL: Triage stage expected ≥3 exit conditions (one per branch), got {len(exit_conds)}"
        )

    routed_targets = {ec.get("exitToStageId") for ec in exit_conds if ec.get("exitToStageId")}
    expected = {approved["id"], rejected["id"], pending["id"]}
    if not expected.issubset(routed_targets):
        sys.exit(
            f"FAIL: Triage exit conditions don't all route to expected stage IDs.\n"
            f"  expected exitToStageId set ⊇ {expected}\n"
            f"  got {routed_targets}"
        )

    exit_types = {ec.get("type") for ec in exit_conds}
    if "wait-for-user" not in exit_types:
        sys.exit(
            f"FAIL: Triage should have a wait-for-user exit condition; "
            f"got types {sorted(t for t in exit_types if t)}"
        )
    if "exit-only" not in exit_types:
        sys.exit(
            f"FAIL: Triage should have an exit-only exit condition; "
            f"got types {sorted(t for t in exit_types if t)}"
        )

    # Every stage carries a process-typed skeleton placeholder task.
    triage_review = _stage_task_by_label(triage, "Triage Review")
    placeholders = {
        "Triage": triage_review,
        "Approved Path": _stage_task_by_label(approved, "Process Approval"),
        "Rejected Path": _stage_task_by_label(rejected, "Record Rejection"),
        "Pending Path": _stage_task_by_label(pending, "Await Confirmation"),
    }
    for stage_name, task in placeholders.items():
        if task.get("type") != "process":
            sys.exit(
                f"FAIL: {stage_name} placeholder task should be type='process'; "
                f"got {task.get('type')!r}"
            )
        if not task_is_skeleton(task):
            sys.exit(
                f"FAIL: {stage_name} placeholder task must be a skeleton (no "
                f"data.name / data.folderPath); got data keys "
                f"{sorted((task.get('data') or {}).keys())}"
            )

    # Pending branch: required-tasks-completed, exit-only, marks-complete:true.
    pending_exit = next(
        (ec for ec in exit_conds if ec.get("exitToStageId") == pending["id"]),
        None,
    )
    if not pending_exit:
        sys.exit(
            "FAIL: cannot find Triage exit condition routing to 'Pending Path'"
        )
    if pending_exit.get("type") != "exit-only":
        sys.exit(
            f"FAIL: Triage→Pending exit should be type='exit-only'; "
            f"got {pending_exit.get('type')!r}"
        )
    if pending_exit.get("marksStageComplete") is not True:
        sys.exit(
            f"FAIL: Triage→Pending exit should have marksStageComplete=true "
            f"(required-tasks-completed is only valid with marks-complete:true); "
            f"got {pending_exit.get('marksStageComplete')!r}"
        )
    pending_rule = first_rule_of_condition(pending_exit)
    if not pending_rule or pending_rule.get("rule") != "required-tasks-completed":
        sys.exit(
            f"FAIL: Triage→Pending exit rule should be 'required-tasks-completed'; "
            f"got {pending_rule and pending_rule.get('rule')!r}"
        )
    if "vars.decision" not in (pending_rule.get("conditionExpression") or ""):
        sys.exit(
            f"FAIL: Triage→Pending exit rule conditionExpression must gate on "
            f"vars.decision; got {pending_rule.get('conditionExpression')!r}"
        )

    # Approved + Rejected branches: selected-tasks-completed, marks-complete:false,
    # each referencing the Triage Review placeholder task.
    triage_review_id = triage_review.get("id")
    for branch_name, branch_node in (
        ("Approved Path", approved),
        ("Rejected Path", rejected),
    ):
        branch_exit = next(
            (ec for ec in exit_conds if ec.get("exitToStageId") == branch_node["id"]),
            None,
        )
        if not branch_exit:
            sys.exit(
                f"FAIL: cannot find Triage exit condition routing to {branch_name!r}"
            )
        if branch_exit.get("marksStageComplete") is not False:
            sys.exit(
                f"FAIL: Triage→{branch_name} exit should have marksStageComplete=false; "
                f"got {branch_exit.get('marksStageComplete')!r}"
            )
        branch_rule = first_rule_of_condition(branch_exit)
        if not branch_rule or branch_rule.get("rule") != "selected-tasks-completed":
            sys.exit(
                f"FAIL: Triage→{branch_name} exit rule should be "
                f"'selected-tasks-completed'; got "
                f"{branch_rule and branch_rule.get('rule')!r}"
            )
        sel_ids = branch_rule.get("selectedTasksIds") or []
        if triage_review_id not in sel_ids:
            sys.exit(
                f"FAIL: Triage→{branch_name} selected-tasks-completed must reference "
                f"the Triage Review task id {triage_review_id!r}; got {sel_ids}"
            )
        if "vars.decision" not in (branch_rule.get("conditionExpression") or ""):
            sys.exit(
                f"FAIL: Triage→{branch_name} exit rule conditionExpression must gate "
                f"on vars.decision; got {branch_rule.get('conditionExpression')!r}"
            )

    approved_entry = list(iter_stage_entry_conditions(approved))
    if not approved_entry:
        sys.exit(
            "FAIL: 'Approved Path' has no entryConditions; expected user-selected-stage"
        )
    rules = [first_rule_of_condition(c) for c in approved_entry]
    rule_types = {r.get("rule") for r in rules if r}
    if "user-selected-stage" not in rule_types:
        sys.exit(
            f"FAIL: 'Approved Path' entry rules should include 'user-selected-stage'; "
            f"got {sorted(rule_types)}"
        )

    # (Edge handle overrides — sourceHandle/targetHandle — were an edge-display
    # concern and are retired along with edges; nothing to assert here.)

    # Structural checks only — no runtime debug. Every task is a process
    # skeleton placeholder (taskTypeId <UNRESOLVED>), so a required/selected
    # task can never complete at runtime and `uip maestro case debug` would
    # never advance past Triage. The task's purpose is structural coverage of
    # the selected-tasks-completed (marks-complete:false) + required-tasks-
    # completed (marks-complete:true) exit rules, which `validate` + the
    # assertions above confirm.
    print(
        "OK: Triage WIDE fan-outs to Approved/Rejected/Pending (3 branches) via "
        "three stage-exit conditions routing through exitToStageId; exits "
        "cover wait-for-user + exit-only(marks-complete:false) + exit-only(marks-"
        "complete:TRUE on Pending); Approved/Rejected gate on selected-tasks-"
        "completed referencing the Triage Review placeholder, Pending on required-"
        "tasks-completed; branch discrimination via conditionExpression on "
        "vars.decision; every stage carries a process-typed skeleton placeholder "
        "task; Approved Path has user-selected-stage entry (edges retired)"
    )


if __name__ == "__main__":
    main()
