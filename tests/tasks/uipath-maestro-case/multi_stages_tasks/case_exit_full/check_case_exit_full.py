#!/usr/bin/env python3
"""CaseExitFull: three case-exit rule-types across both marks-case-complete shapes."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    _get_ci,
    assert_count,
    assert_tasks_nested,
    find_node_by_label,
    find_stages,
    first_rule_of_condition,
    get_case_exit_conditions,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    read_caseplan,
    start_debug,
)


def _is_required(stage: dict) -> bool | None:
    return (stage.get("data") or {}).get("isRequired")


def _task_count(stage: dict) -> int:
    lanes = (stage.get("data") or {}).get("tasks") or []
    return sum(len(lane) for lane in lanes if isinstance(lane, list))


def main():
    plan = read_caseplan()

    stages = find_stages(plan, include_exception=False)
    assert_count(len(stages), 3, "regular stage(s)")

    intake = find_node_by_label(plan, "Intake")
    audit = find_node_by_label(plan, "Audit")
    archive = find_node_by_label(plan, "Archive")

    expected_required = {
        "Intake": (intake, True),
        "Audit": (audit, False),
        "Archive": (archive, True),
    }
    for name, (stage, want) in expected_required.items():
        got = _is_required(stage)
        if got is not want:
            sys.exit(
                f"FAIL: stage {name!r} isRequired should be {want}; got {got!r}"
            )

    assert_tasks_nested(plan)
    for name, (stage, _want) in expected_required.items():
        n = _task_count(stage)
        if n < 1:
            sys.exit(
                f"FAIL: stage {name!r} must carry ≥1 task (placeholder) for its "
                f"required-tasks-completed completion condition; got {n}"
            )

    audit_entry = list(iter_stage_entry_conditions(audit))
    if not audit_entry:
        sys.exit("FAIL: Audit has no entryConditions; expected selected-stage-completed")
    rule = first_rule_of_condition(audit_entry[0])
    if not rule or rule.get("rule") != "selected-stage-completed":
        sys.exit(
            f"FAIL: Audit entry rule should be 'selected-stage-completed'; "
            f"got {rule and rule.get('rule')!r}"
        )

    audit_exits = list(iter_stage_exit_conditions(audit))
    handoff = next(
        (
            ec
            for ec in audit_exits
            if (first_rule_of_condition(ec) or {}).get("rule")
            == "selected-tasks-completed"
        ),
        None,
    )
    if handoff is None:
        sys.exit(
            "FAIL: Audit must carry a selected-tasks-completed stage-exit hand-off; "
            f"got exit rules {[ (first_rule_of_condition(ec) or {}).get('rule') for ec in audit_exits ]}"
        )
    if handoff.get("exitToStageId") != archive["id"]:
        sys.exit(
            f"FAIL: Audit stage-exit must route to Archive id {archive['id']!r}; "
            f"got exitToStageId {handoff.get('exitToStageId')!r}"
        )
    if handoff.get("marksStageComplete") is not False:
        sys.exit(
            "FAIL: Audit selected-tasks-completed stage-exit must have "
            f"marksStageComplete=false; got {handoff.get('marksStageComplete')!r}"
        )

    if _task_count(audit) < 2:
        sys.exit(
            f"FAIL: Audit must carry ≥2 tasks (placeholder + handoff); "
            f"got {_task_count(audit)}"
        )

    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) < 3:
        sys.exit(
            f"FAIL: expected ≥3 case-exit conditions covering three rule-types; "
            f"got {len(case_exits)}"
        )

    completing_rules: set[str] = set()
    non_completing_rules: set[str] = set()
    selected_stage_by_rule: dict[str, set[str]] = {}

    for ce in case_exits:
        rule = first_rule_of_condition(ce) or {}
        rname = rule.get("rule")
        marks = ce.get("marksCaseComplete")
        if marks is True:
            completing_rules.add(rname)
        elif marks is False:
            non_completing_rules.add(rname)
        if rname in ("selected-stage-exited", "selected-stage-completed"):
            sid = rule.get("selectedStageId")
            if sid:
                selected_stage_by_rule.setdefault(rname, set()).add(sid)

    if "required-stages-completed" not in completing_rules:
        sys.exit(
            f"FAIL: missing completing case-exit 'required-stages-completed'; "
            f"got marksCaseComplete=true rules {sorted(r for r in completing_rules if r)}"
        )

    if "selected-stage-exited" not in non_completing_rules:
        sys.exit(
            f"FAIL: missing non-completing case-exit 'selected-stage-exited'; "
            f"got marksCaseComplete=false rules "
            f"{sorted(r for r in non_completing_rules if r)}"
        )
    if "selected-stage-completed" not in non_completing_rules:
        sys.exit(
            f"FAIL: missing non-completing case-exit 'selected-stage-completed'; "
            f"got marksCaseComplete=false rules "
            f"{sorted(r for r in non_completing_rules if r)}"
        )

    if audit["id"] not in selected_stage_by_rule.get("selected-stage-exited", set()):
        sys.exit(
            f"FAIL: selected-stage-exited case-exit must reference Audit id "
            f"{audit['id']!r}; got {selected_stage_by_rule.get('selected-stage-exited')}"
        )
    if archive["id"] not in selected_stage_by_rule.get("selected-stage-completed", set()):
        sys.exit(
            f"FAIL: selected-stage-completed case-exit must reference Archive id "
            f"{archive['id']!r}; got {selected_stage_by_rule.get('selected-stage-completed')}"
        )

    payload = start_debug(timeout=540)
    status = _get_ci(payload, "finalStatus", "FinalStatus", "status", "Status")

    print(
        "OK: 3 stages with mixed isRequired (Intake/Archive true, Audit false); "
        "Audit has selected-stage-completed stage-entry; case-level exits cover "
        "three rule-types — required-stages-completed (true); selected-stage-exited "
        "Audit + selected-stage-completed Archive (false); debug payload returned "
        f"(status={status})"
    )


if __name__ == "__main__":
    main()
