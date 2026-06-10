#!/usr/bin/env python3
"""FanInJoin: diamond topology with two parallel branches joining at Join."""

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
    iter_stage_entry_conditions,
    read_caseplan,
    start_debug,
    task_is_skeleton,
)


def main():
    plan = read_caseplan()

    triggers = find_triggers(plan)
    assert_count(len(triggers), 1, "trigger node(s)")

    stages = find_stages(plan, include_exception=False)
    assert_count(len(stages), 4, "regular stage(s)")

    triage = find_node_by_label(plan, "Triage")
    validate = find_node_by_label(plan, "Validate")
    enrich = find_node_by_label(plan, "Enrich")
    join = find_node_by_label(plan, "Join")

    # Reachability is condition-driven (edges retired): Triage is the case start
    # (case-entered); Validate & Enrich are reached from Triage via their
    # selected-stage-completed entry rules; Join fans in from both (asserted via
    # Join's two entry rules below). No trigger→stage edge.
    triage_entry = list(iter_stage_entry_conditions(triage))
    triage_rules = {(first_rule_of_condition(c) or {}).get("rule") for c in triage_entry}
    if "case-entered" not in triage_rules:
        sys.exit(
            f"FAIL: 'Triage' must carry a case-entered entry condition; "
            f"got entry rules {sorted(r for r in triage_rules if r)}"
        )
    if not find_transitions(plan, source=triage["id"], target=validate["id"]):
        sys.exit(
            "FAIL: no Triage → Validate transition; Validate's entry must name "
            "Triage (selected-stage-completed selectedStageId=Triage)"
        )
    if not find_transitions(plan, source=triage["id"], target=enrich["id"]):
        sys.exit(
            "FAIL: no Triage → Enrich transition; Enrich's entry must name "
            "Triage (selected-stage-completed selectedStageId=Triage)"
        )

    join_entry = list(iter_stage_entry_conditions(join))
    if len(join_entry) < 2:
        sys.exit(
            f"FAIL: Join must declare ≥2 entryConditions (one per upstream); got {len(join_entry)}"
        )

    referenced_stage_ids = set()
    for cond in join_entry:
        rule = first_rule_of_condition(cond)
        if not rule:
            continue
        if rule.get("rule") != "selected-stage-completed":
            sys.exit(
                f"FAIL: Join entry rule must be 'selected-stage-completed'; got {rule.get('rule')!r}"
            )
        sid = rule.get("selectedStageId")
        if sid:
            referenced_stage_ids.add(sid)

    if not {validate["id"], enrich["id"]}.issubset(referenced_stage_ids):
        sys.exit(
            f"FAIL: Join entry rules must reference both Validate and Enrich stage IDs; "
            f"got {referenced_stage_ids}"
        )

    expected_skeleton_types_per_stage = {
        "Triage": {"rpa", "api-workflow"},
        "Validate": {"agent"},
        "Enrich": {"agent"},
        "Join": {"case-management"},
    }
    for stage_label, want_types in expected_skeleton_types_per_stage.items():
        stage = find_node_by_label(plan, stage_label)
        lanes = (stage.get("data") or {}).get("tasks") or []
        tasks_in_stage = [t for lane in lanes for t in (lane or [])]
        types_seen = {(t.get("type") or "?") for t in tasks_in_stage}
        missing = want_types - types_seen
        if missing:
            sys.exit(
                f"FAIL: stage {stage_label!r} should contain skeleton task(s) of "
                f"type(s) {sorted(want_types)}; missing {sorted(missing)} "
                f"(saw {sorted(types_seen)})"
            )
        for want_type in want_types:
            skeleton = next(t for t in tasks_in_stage if t.get("type") == want_type)
            if not task_is_skeleton(skeleton):
                data = skeleton.get("data") or {}
                sys.exit(
                    f"FAIL: stage {stage_label!r} task type {want_type!r} should "
                    f"be a skeleton — must NOT carry resource wiring "
                    f"(data.name/data.folderPath for non-connector tasks; "
                    f"data.inputs for action; data.typeId/connectionId for "
                    f"connector tasks); got data keys {sorted(data.keys())}"
                )

    payload = start_debug(timeout=540)
    status = _get_ci(payload, "finalStatus", "FinalStatus", "status", "Status")

    print(
        "OK: diamond topology Triage→{Validate,Enrich}→Join with two "
        "selected-stage-completed entry rules on Join referencing both upstream "
        "stages; 5 skeleton tasks across 4 stages span 4 plugin types "
        "(Triage:{rpa, api-workflow}, Validate:agent, Enrich:agent, "
        f"Join:case-management); debug payload returned (status={status})"
    )


if __name__ == "__main__":
    main()
