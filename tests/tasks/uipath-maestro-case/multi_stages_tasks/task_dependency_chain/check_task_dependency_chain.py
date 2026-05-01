#!/usr/bin/env python3
"""TaskDependencyChain: task-driven exits + under-covered task-entry rule-types."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    find_node_by_label,
    find_stages,
    first_rule_of_condition,
    get_root,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    read_caseplan,
)


def _stage_task_by_label(stage: dict, label: str) -> dict:
    lanes = (stage.get("data") or {}).get("tasks") or []
    for lane in lanes:
        for task in lane or []:
            if (task or {}).get("displayName") == label or (task or {}).get("label") == label:
                return task
    labels = [
        (t or {}).get("displayName") or (t or {}).get("label")
        for lane in lanes
        for t in (lane or [])
    ]
    sys.exit(
        f"FAIL: task with displayName/label={label!r} not found in stage "
        f"{(stage.get('data') or {}).get('label')!r}; saw {labels}"
    )


def _task_entry_rule(task: dict) -> str | None:
    conds = task.get("entryConditions") or []
    for cond in conds:
        rule = first_rule_of_condition(cond)
        if rule and rule.get("rule") not in (None, "current-stage-entered"):
            return rule.get("rule")
    if conds:
        rule = first_rule_of_condition(conds[0])
        return rule.get("rule") if rule else None
    return None


def main():
    plan = read_caseplan()

    stages = find_stages(plan, include_exception=False)
    if len(stages) != 3:
        sys.exit(f"FAIL: expected 3 regular stages, got {len(stages)}")

    process = find_node_by_label(plan, "Process")
    finalize = find_node_by_label(plan, "Finalize")
    done = find_node_by_label(plan, "Done")

    process_exits = list(iter_stage_exit_conditions(process))
    process_exit_rules = {
        (first_rule_of_condition(c) or {}).get("rule") for c in process_exits
    }
    if "required-tasks-completed" not in process_exit_rules:
        sys.exit(
            f"FAIL: Process should have exit rule 'required-tasks-completed'; "
            f"got {sorted(r for r in process_exit_rules if r)}"
        )

    finalize_exits = list(iter_stage_exit_conditions(finalize))
    finalize_exit_rules = {
        (first_rule_of_condition(c) or {}).get("rule") for c in finalize_exits
    }
    if "selected-tasks-completed" not in finalize_exit_rules:
        sys.exit(
            f"FAIL: Finalize should have exit rule 'selected-tasks-completed'; "
            f"got {sorted(r for r in finalize_exit_rules if r)}"
        )
    routed_targets = {ec.get("exitToStageId") for ec in finalize_exits if ec.get("exitToStageId")}
    if done["id"] not in routed_targets:
        sys.exit(
            f"FAIL: Finalize selected-tasks-completed exit must route to Done "
            f"(id={done['id']!r}); got exitToStageId set {routed_targets}"
        )
    if not any(ec.get("marksStageComplete") is False for ec in finalize_exits):
        sys.exit("FAIL: Finalize selected-tasks-completed exit must have marksStageComplete=false")

    finalize_entries = list(iter_stage_entry_conditions(finalize))
    finalize_entry_rules = {
        (first_rule_of_condition(c) or {}).get("rule") for c in finalize_entries
    }
    if "selected-stage-completed" not in finalize_entry_rules:
        sys.exit(
            f"FAIL: Finalize should have entry rule 'selected-stage-completed'; "
            f"got {sorted(r for r in finalize_entry_rules if r)}"
        )

    first_step = _stage_task_by_label(process, "First Step")
    second_step = _stage_task_by_label(process, "Second Step")
    region_check = _stage_task_by_label(finalize, "Region Check")
    final_task = _stage_task_by_label(finalize, "Final Task")
    optional_audit = _stage_task_by_label(finalize, "Optional Audit")

    expectations = {
        "First Step": (first_step, "runs-sequentially"),
        "Second Step": (second_step, "runs-sequentially"),
        "Region Check": (region_check, "wait-for-connector"),
        "Final Task": (final_task, "selected-tasks-completed"),
        "Optional Audit": (optional_audit, "adhoc"),
    }
    for name, (task, want) in expectations.items():
        got = _task_entry_rule(task)
        if got != want:
            sys.exit(
                f"FAIL: task {name!r} task-entry rule should be {want!r}; got {got!r}"
            )

    if optional_audit.get("type") != "process":
        sys.exit(
            f"FAIL: 'Optional Audit' should be a process-typed skeleton task; "
            f"got type={optional_audit.get('type')!r}"
        )
    oa_data = optional_audit.get("data") or {}
    oa_ctx = oa_data.get("context") or {}
    if oa_ctx.get("taskTypeId"):
        sys.exit(
            f"FAIL: 'Optional Audit' is a skeleton task — must NOT have "
            f"data.context.taskTypeId set; got {oa_ctx.get('taskTypeId')!r}"
        )

    fs_data = first_step.get("data") or {}
    fs_repeat = fs_data.get("repeat")
    if fs_repeat != 5:
        sys.exit(
            f"FAIL: 'First Step' wait-for-timer should have data.repeat=5 "
            f"(bounded repeat flag); got {fs_repeat!r}"
        )

    ss_data = second_step.get("data") or {}
    if ss_data.get("timerType") != "timeCycle":
        sys.exit(
            f"FAIL: 'Second Step' wait-for-timer should use the timeCycle "
            f"branch (data.timerType='timeCycle'); got "
            f"{ss_data.get('timerType')!r}"
        )
    if ss_data.get("timeCycle") != "R3/PT2H":
        sys.exit(
            f"FAIL: 'Second Step' data.timeCycle should be 'R3/PT2H'; "
            f"got {ss_data.get('timeCycle')!r}"
        )

    rc_conds = region_check.get("entryConditions") or []
    rc_rule = first_rule_of_condition(rc_conds[0]) if rc_conds else None
    expr = (rc_rule or {}).get("conditionExpression") or ""
    if "vars.region" not in expr:
        sys.exit(
            f"FAIL: 'Region Check' wait-for-connector conditionExpression must reference vars.region; got {expr!r}"
        )
    if "vars.priorityScore" not in expr:
        sys.exit(
            f"FAIL: 'Region Check' wait-for-connector conditionExpression must reference vars.priorityScore; got {expr!r}"
        )
    if "metadata.tier" not in expr:
        sys.exit(
            f"FAIL: 'Region Check' wait-for-connector conditionExpression must reference metadata.tier (=metadata.X form); got {expr!r}"
        )

    ft_conds = final_task.get("entryConditions") or []
    ft_rule = first_rule_of_condition(ft_conds[0]) if ft_conds else None
    sel_ids = (ft_rule or {}).get("selectedTasksIds") or []
    if region_check.get("id") not in sel_ids:
        sys.exit(
            f"FAIL: 'Final Task' selected-tasks-completed must reference Region Check id "
            f"{region_check.get('id')!r}; got {sel_ids}"
        )

    root = get_root(plan)
    io_vars = (((root.get("data") or {}).get("uipath") or {}).get("variables") or {}).get(
        "inputOutputs"
    ) or []
    region = next(
        (v for v in io_vars if v.get("id") == "region" or v.get("name") == "region"),
        None,
    )
    if not region:
        names = [v.get("name") for v in io_vars]
        sys.exit(f"FAIL: missing root variable 'region'; got {names}")
    if region.get("type") != "string":
        sys.exit(f"FAIL: variable 'region' should be type=string; got {region.get('type')!r}")

    priority = next(
        (v for v in io_vars if v.get("id") == "priorityScore" or v.get("name") == "priorityScore"),
        None,
    )
    if not priority:
        names = [v.get("name") for v in io_vars]
        sys.exit(f"FAIL: missing root variable 'priorityScore'; got {names}")
    if priority.get("type") != "number":
        sys.exit(
            f"FAIL: variable 'priorityScore' should be type=number; "
            f"got {priority.get('type')!r}"
        )

    print(
        "OK: Process exit required-tasks-completed; Finalize exit "
        "selected-tasks-completed→Done (marksStageComplete=false); Finalize "
        "entry selected-stage-completed; task-entry rules cover runs-sequentially/"
        "adhoc/wait-for-connector(vars.region+vars.priorityScore+metadata.tier)/"
        "selected-tasks-completed; First Step uses timeDuration+repeat=5; "
        "Second Step uses timeCycle R3/PT2H; root variables 'region' (string) "
        "and 'priorityScore' (number); 'Optional Audit' is a process-typed "
        "skeleton task with empty data.context"
    )


if __name__ == "__main__":
    main()
