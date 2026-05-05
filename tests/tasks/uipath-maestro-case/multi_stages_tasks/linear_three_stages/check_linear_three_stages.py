#!/usr/bin/env python3
"""LinearThreeStages: 3 regular stages chained linearly behind a manual trigger."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_count,
    find_edges,
    find_node_by_label,
    find_stages,
    find_triggers,
    first_rule_of_condition,
    get_root,
    iter_stage_entry_conditions,
    iter_tasks,
    read_caseplan,
)


def main():
    plan = read_caseplan()

    triggers = find_triggers(plan)
    assert_count(len(triggers), 1, "trigger node(s)")

    stages = find_stages(plan, include_exception=False)
    assert_count(len(stages), 3, "regular stage(s)")

    intake = find_node_by_label(plan, "Intake")
    review = find_node_by_label(plan, "Review")
    decision = find_node_by_label(plan, "Decision")

    edges = plan.get("edges") or []
    assert_count(len(edges), 3, "edge(s)")

    trigger_edges = [e for e in edges if e.get("type") == "case-management:TriggerEdge"]
    stage_edges = [e for e in edges if e.get("type") == "case-management:Edge"]
    assert_count(len(trigger_edges), 1, "TriggerEdge(s)")
    assert_count(len(stage_edges), 2, "stage Edge(s)")

    if not find_edges(plan, source=triggers[0]["id"], target=intake["id"]):
        sys.exit(f"FAIL: missing TriggerEdge {triggers[0]['id']} → {intake['id']} (Intake)")
    intake_review = find_edges(plan, source=intake["id"], target=review["id"])
    if not intake_review:
        sys.exit("FAIL: missing Edge Intake → Review")
    review_decision = find_edges(plan, source=review["id"], target=decision["id"])
    if not review_decision:
        sys.exit("FAIL: missing Edge Review → Decision")

    intake_review_label = (intake_review[0].get("data") or {}).get("label") or ""
    review_decision_label = (review_decision[0].get("data") or {}).get("label") or ""
    if intake_review_label.strip().lower() != "review":
        sys.exit(
            f"FAIL: Intake→Review edge label should be 'Review' (single-outbound "
            f"edge label inference rule #3 = target stage name); got {intake_review_label!r}"
        )
    if review_decision_label.strip().lower() != "decision":
        sys.exit(
            f"FAIL: Review→Decision edge label should be 'Decision' (single-outbound "
            f"edge label inference rule #3 = target stage name); got {review_decision_label!r}"
        )

    intake_entry = list(iter_stage_entry_conditions(intake))
    if not intake_entry:
        sys.exit("FAIL: Intake has no entryConditions; expected explicit case-entered rule")
    rule = first_rule_of_condition(intake_entry[0])
    if not rule or rule.get("rule") != "case-entered":
        sys.exit(
            f"FAIL: Intake entry rule should be 'case-entered'; "
            f"got {rule and rule.get('rule')!r}"
        )

    timer_tasks = [t for t in iter_tasks(plan) if t.get("type") == "wait-for-timer"]
    if not timer_tasks:
        types_seen = sorted({t.get("type", "?") for t in iter_tasks(plan)})
        sys.exit(f"FAIL: no wait-for-timer task in caseplan. Types seen: {types_seen}")

    review_lanes = (review.get("data") or {}).get("tasks") or []
    timer_lane_indices = {
        lane_idx
        for lane_idx, lane in enumerate(review_lanes)
        for t in (lane or [])
        if t.get("type") == "wait-for-timer"
    }
    review_task_ids = {t.get("id") for lane in review_lanes for t in (lane or [])}
    review_timers = [t for t in timer_tasks if t.get("id") in review_task_ids]
    if len(review_timers) < 2:
        labels = [(t or {}).get("displayName") or (t or {}).get("label") for t in review_timers]
        sys.exit(
            f"FAIL: Review should have ≥2 parallel wait-for-timer tasks "
            f"('Hold For 1 Hour' + 'Notify Reviewer'); got {len(review_timers)} ({labels})"
        )
    if len(timer_lane_indices) < 2:
        sys.exit(
            f"FAIL: Review's two timer tasks must occupy distinct lanes in "
            f"data.tasks (parallel layout); got lane indices {sorted(timer_lane_indices)}"
        )

    def _by_label(label: str) -> dict | None:
        for t in review_timers:
            if (t.get("displayName") or t.get("label")) == label:
                return t
        return None

    hold = _by_label("Hold For 1 Hour")
    notify = _by_label("Notify Reviewer")
    if not hold or not notify:
        labels = [(t.get("displayName") or t.get("label")) for t in review_timers]
        sys.exit(
            f"FAIL: Review timers must include 'Hold For 1 Hour' and "
            f"'Notify Reviewer'; got {labels}"
        )

    if hold.get("shouldRunOnlyOnce") is not True:
        sys.exit(
            f"FAIL: 'Hold For 1 Hour' should have shouldRunOnlyOnce=true; "
            f"got {hold.get('shouldRunOnlyOnce')!r}"
        )
    skip = hold.get("skipCondition")
    if not isinstance(skip, str) or "skipReview" not in skip:
        sys.exit(
            f"FAIL: 'Hold For 1 Hour' skipCondition should reference skipReview; "
            f"got {skip!r}"
        )
    if notify.get("isRequired") is not False:
        sys.exit(
            f"FAIL: 'Notify Reviewer' should have isRequired=false (task-level "
            f"flag explicitly set); got {notify.get('isRequired')!r}"
        )

    for label, task in (("Hold For 1 Hour", hold), ("Notify Reviewer", notify)):
        conds = task.get("entryConditions") or []
        if not conds:
            sys.exit(
                f"FAIL: {label!r} has no entryConditions; expected "
                f"current-stage-entered task-entry condition"
            )
        rule = first_rule_of_condition(conds[0])
        if not rule or rule.get("rule") != "current-stage-entered":
            sys.exit(
                f"FAIL: {label!r} task-entry rule should be "
                f"'current-stage-entered'; got {rule and rule.get('rule')!r}"
            )

    root = get_root(plan)
    variables = ((root.get("data") or {}).get("uipath") or {}).get("variables") or {}
    io_vars = variables.get("inputOutputs") or []
    in_vars = variables.get("inputs") or []
    out_vars = variables.get("outputs") or []

    if not any(v.get("id") == "skipReview" or v.get("name") == "skipReview" for v in io_vars):
        names = [v.get("name") for v in io_vars]
        sys.exit(
            f"FAIL: root.data.uipath.variables.inputOutputs missing "
            f"'skipReview' Variable; got {names}"
        )

    if not any(v.get("name") == "caseRef" and v.get("type") == "string" for v in in_vars):
        names = [(v.get("name"), v.get("type")) for v in in_vars]
        sys.exit(
            f"FAIL: root.data.uipath.variables.inputs missing string In "
            f"argument 'caseRef'; got {names}"
        )
    if not any(v.get("name") == "caseRef" for v in io_vars):
        sys.exit(
            "FAIL: In argument 'caseRef' is missing its inputOutputs companion entry"
        )

    trigger_outputs = ((triggers[0].get("data") or {}).get("uipath") or {}).get("outputs") or []
    if not any(o.get("name") == "caseRef" and o.get("var") == "caseRef" for o in trigger_outputs):
        sys.exit(
            f"FAIL: trigger node missing data.uipath.outputs entry for In argument "
            f"'caseRef'; got {[(o.get('name'), o.get('var')) for o in trigger_outputs]}"
        )

    if not any(v.get("name") == "finalDecision" and v.get("type") == "string" for v in out_vars):
        names = [(v.get("name"), v.get("type")) for v in out_vars]
        sys.exit(
            f"FAIL: root.data.uipath.variables.outputs missing string Out "
            f"argument 'finalDecision'; got {names}"
        )
    if not any(v.get("name") == "finalDecision" for v in io_vars):
        sys.exit(
            "FAIL: Out argument 'finalDecision' is missing its inputOutputs companion entry"
        )

    expected_var_types = {
        "dueDate": "date",
        "caseMetadata": "object",
        "attachments": "array",
        "caseSchema": "jsonSchema",
    }
    for var_name, want_type in expected_var_types.items():
        match = next(
            (v for v in io_vars if v.get("name") == var_name or v.get("id") == var_name),
            None,
        )
        if not match:
            names = [(v.get("name"), v.get("type")) for v in io_vars]
            sys.exit(
                f"FAIL: missing root variable {var_name!r} (expected type {want_type!r}); "
                f"got {names}"
            )
        if match.get("type") != want_type:
            sys.exit(
                f"FAIL: variable {var_name!r} should be type={want_type!r}; "
                f"got {match.get('type')!r}"
            )

    print(
        "OK: 3 stages (Intake → Review → Decision) with single-outbound edge "
        "labels matching target stage names (rule #3); case-entered on Intake; "
        "TWO parallel wait-for-timer tasks on Review in distinct lanes — "
        "'Hold For 1 Hour' (shouldRunOnlyOnce + skipCondition =vars.skipReview) "
        "and 'Notify Reviewer' (isRequired=false) — both carrying "
        "current-stage-entered task-entry; root has all 7 Variable types "
        "(boolean skipReview, string caseRef In + finalDecision Out, date "
        "dueDate, object caseMetadata, array attachments, jsonSchema caseSchema) "
        "with caseRef bridged through trigger output mapping"
    )


if __name__ == "__main__":
    main()
