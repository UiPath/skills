#!/usr/bin/env python3
"""LinearThreeStages: 3 regular stages chained linearly behind a manual trigger."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    _get_ci,
    assert_count,
    find_node_by_label,
    find_stages,
    find_transitions,
    find_triggers,
    first_rule_of_condition,
    get_variables,
    iter_stage_entry_conditions,
    iter_tasks,
    read_caseplan,
    start_debug,
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

    # Reachability is condition-driven (edges retired): Intake is the case start
    # via case-entered; Review and Decision are reached via selected-stage-*
    # entry rules naming the upstream stage. No trigger→stage edge.
    if not find_transitions(plan, source=intake["id"], target=review["id"]):
        sys.exit(
            "FAIL: no Intake → Review transition; Review's entry condition must "
            "name Intake (selected-stage-completed/-exited selectedStageId=Intake)"
        )
    if not find_transitions(plan, source=review["id"], target=decision["id"]):
        sys.exit(
            "FAIL: no Review → Decision transition; Decision's entry condition must "
            "name Review (selected-stage-completed/-exited selectedStageId=Review)"
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

    variables = get_variables(plan)
    io_vars = variables.get("inputOutputs") or []
    in_vars = variables.get("inputs") or []
    out_vars = variables.get("outputs") or []

    if not any(v.get("id") == "skipReview" or v.get("name") == "skipReview" for v in io_vars):
        names = [v.get("name") for v in io_vars]
        sys.exit(
            f"FAIL: variables.inputOutputs missing 'skipReview' Variable; "
            f"got {names}"
        )

    if not any(v.get("name") == "caseRef" and v.get("type") == "string" for v in in_vars):
        names = [(v.get("name"), v.get("type")) for v in in_vars]
        sys.exit(
            f"FAIL: variables.inputs missing string In argument 'caseRef'; "
            f"got {names}"
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
            f"FAIL: variables.outputs missing string Out argument 'finalDecision'; "
            f"got {names}"
        )
    if not any(v.get("name") == "finalDecision" for v in io_vars):
        sys.exit(
            "FAIL: Out argument 'finalDecision' is missing its inputOutputs companion entry"
        )

    def _find_io(var_name: str) -> dict | None:
        return next(
            (v for v in io_vars if v.get("name") == var_name or v.get("id") == var_name),
            None,
        )

    # Top-level `type` field (platform enum: string/integer/float/double/
    # boolean/datetime/date/jsonSchema/file). `object` and `array` are NOT
    # top-level types — object/array-shaped variables are type='jsonSchema'
    # with the shape carried in body.type (asserted below).
    expected_top_types = {
        "dueDate": "date",
    }
    for var_name, want_type in expected_top_types.items():
        match = _find_io(var_name)
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

    # Structured variables: type='jsonSchema', object vs array distinction
    # lives in the body schema (body.type), not the top-level type.
    expected_schema_body_types = {
        "caseMetadata": "object",
        "attachments": "array",
        "caseSchema": "object",
    }
    for var_name, want_body_type in expected_schema_body_types.items():
        match = _find_io(var_name)
        if not match:
            names = [(v.get("name"), v.get("type")) for v in io_vars]
            sys.exit(
                f"FAIL: missing root variable {var_name!r} "
                f"(expected jsonSchema with body.type={want_body_type!r}); got {names}"
            )
        if match.get("type") != "jsonSchema":
            sys.exit(
                f"FAIL: variable {var_name!r} should be type='jsonSchema' "
                f"(object/array shape lives in body.type); got {match.get('type')!r}"
            )
        body = match.get("body") or {}
        if body.get("type") != want_body_type:
            sys.exit(
                f"FAIL: variable {var_name!r} jsonSchema body.type should be "
                f"{want_body_type!r}; got {body.get('type')!r}"
            )

    payload = start_debug(timeout=540)
    status = _get_ci(payload, "finalStatus", "FinalStatus", "status", "Status")

    print(
        "OK: 3 stages (Intake → Review → Decision) chained via condition-driven "
        "transitions (Review←Intake, Decision←Review via selected-stage-completed); "
        "case-entered on Intake; "
        "TWO parallel wait-for-timer tasks on Review in distinct lanes — "
        "'Hold For 1 Hour' (shouldRunOnlyOnce + skipCondition =vars.skipReview) "
        "and 'Notify Reviewer' (isRequired=false) — both carrying "
        "current-stage-entered task-entry; root has all 7 variables "
        "(boolean skipReview, string caseRef In + finalDecision Out, date "
        "dueDate, jsonSchema caseMetadata[body=object], attachments[body=array], "
        "caseSchema[body=object]) "
        f"with caseRef bridged through trigger output mapping; debug payload "
        f"returned (status={status})"
    )


if __name__ == "__main__":
    main()
