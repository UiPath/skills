#!/usr/bin/env python3
"""CaseExitFull: full case-exit rule-type matrix + wait-for-connector stage-entry."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_count,
    find_node_by_label,
    find_stages,
    first_rule_of_condition,
    get_case_exit_conditions,
    iter_stage_entry_conditions,
    read_caseplan,
)


def _is_required(stage: dict) -> bool | None:
    return (stage.get("data") or {}).get("isRequired")


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

    audit_entry = list(iter_stage_entry_conditions(audit))
    if not audit_entry:
        sys.exit("FAIL: Audit has no entryConditions; expected wait-for-connector")
    rule = first_rule_of_condition(audit_entry[0])
    if not rule or rule.get("rule") != "wait-for-connector":
        sys.exit(
            f"FAIL: Audit entry rule should be 'wait-for-connector'; "
            f"got {rule and rule.get('rule')!r}"
        )
    expr = rule.get("conditionExpression") or ""
    if "submission" not in expr:
        sys.exit(
            f"FAIL: Audit wait-for-connector conditionExpression should mention "
            f"'submission'; got {expr!r}"
        )

    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) < 4:
        sys.exit(
            f"FAIL: expected ≥4 case-exit conditions covering all rule-types; "
            f"got {len(case_exits)}"
        )

    completing_rules: set[str] = set()
    non_completing_rules: set[str] = set()
    selected_stage_by_rule: dict[str, set[str]] = {}
    cancel_expr = ""

    for ce in case_exits:
        rule = first_rule_of_condition(ce) or {}
        rname = rule.get("rule")
        marks = ce.get("marksCaseComplete")
        if marks is True:
            completing_rules.add(rname)
        elif marks is False:
            non_completing_rules.add(rname)
        if rname == "wait-for-connector":
            cancel_expr = rule.get("conditionExpression") or cancel_expr
        if rname in ("selected-stage-exited", "selected-stage-completed"):
            sid = rule.get("selectedStageId")
            if sid:
                selected_stage_by_rule.setdefault(rname, set()).add(sid)

    if "required-stages-completed" not in completing_rules:
        sys.exit(
            f"FAIL: missing completing case-exit 'required-stages-completed'; "
            f"got marksCaseComplete=true rules {sorted(r for r in completing_rules if r)}"
        )
    if "wait-for-connector" not in completing_rules:
        sys.exit(
            f"FAIL: missing completing case-exit 'wait-for-connector'; "
            f"got marksCaseComplete=true rules {sorted(r for r in completing_rules if r)}"
        )
    if "cancel" not in cancel_expr.lower():
        sys.exit(
            f"FAIL: case-exit wait-for-connector conditionExpression should mention "
            f"'cancel'; got {cancel_expr!r}"
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

    print(
        "OK: 3 stages with mixed isRequired (Intake/Archive true, Audit false); "
        "Audit has wait-for-connector stage-entry; root case-exits cover all 4 "
        "rule-types — required-stages-completed + wait-for-connector cancel "
        "(true); selected-stage-exited Audit + selected-stage-completed "
        "Archive (false)"
    )


if __name__ == "__main__":
    main()
