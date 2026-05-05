#!/usr/bin/env python3
"""FanInJoin: diamond topology with two parallel branches joining at Join."""

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
    iter_stage_entry_conditions,
    read_caseplan,
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

    if not find_edges(plan, source=triggers[0]["id"], target=triage["id"]):
        sys.exit(f"FAIL: missing TriggerEdge {triggers[0]['id']} → Triage")
    if not find_edges(plan, source=triage["id"], target=validate["id"]):
        sys.exit("FAIL: missing edge Triage → Validate")
    if not find_edges(plan, source=triage["id"], target=enrich["id"]):
        sys.exit("FAIL: missing edge Triage → Enrich")
    if not find_edges(plan, source=validate["id"], target=join["id"]):
        sys.exit("FAIL: missing edge Validate → Join")
    if not find_edges(plan, source=enrich["id"], target=join["id"]):
        sys.exit("FAIL: missing edge Enrich → Join")

    inbound_to_join = find_edges(plan, target=join["id"])
    if len(inbound_to_join) < 2:
        sys.exit(
            f"FAIL: Join must have ≥2 inbound stage edges (fan-in); got {len(inbound_to_join)}"
        )
    inbound_sources = {e.get("source") for e in inbound_to_join}
    if not {validate["id"], enrich["id"]}.issubset(inbound_sources):
        sys.exit(
            f"FAIL: Join inbound sources must include Validate and Enrich; got {inbound_sources}"
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
        "Validate": {"action"},
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
            data = skeleton.get("data") or {}
            ctx = data.get("context") or {}
            if ctx.get("taskTypeId") or data.get("typeId") or data.get("connectionId"):
                sys.exit(
                    f"FAIL: stage {stage_label!r} task type {want_type!r} should "
                    f"be a skeleton (empty data) — must NOT have taskTypeId/typeId/"
                    f"connectionId; got data keys {sorted(data.keys())}"
                )

    print(
        "OK: diamond topology Triage→{Validate,Enrich}→Join with two "
        "selected-stage-completed entry rules on Join referencing both upstream "
        "stages; 5 skeleton tasks across 4 stages cover 5 plugin types "
        "(Triage:{rpa, api-workflow}, Validate:action, Enrich:agent, "
        "Join:case-management) all with empty data"
    )


if __name__ == "__main__":
    main()
