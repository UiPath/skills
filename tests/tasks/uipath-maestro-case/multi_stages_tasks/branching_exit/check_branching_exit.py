#!/usr/bin/env python3
"""BranchingExit: Triage routes to Approved/Rejected via two exit conditions."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_count,
    edge_labels_from,
    find_edges,
    find_node_by_label,
    find_stages,
    first_rule_of_condition,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    read_caseplan,
)


def main():
    plan = read_caseplan()

    stages = find_stages(plan, include_exception=False)
    assert_count(len(stages), 4, "regular stage(s)")

    triage = find_node_by_label(plan, "Triage")
    approved = find_node_by_label(plan, "Approved Path")
    rejected = find_node_by_label(plan, "Rejected Path")
    pending = find_node_by_label(plan, "Pending Path")

    if not find_edges(plan, source=triage["id"], target=approved["id"]):
        sys.exit("FAIL: no edge Triage → Approved Path")
    if not find_edges(plan, source=triage["id"], target=rejected["id"]):
        sys.exit("FAIL: no edge Triage → Rejected Path")
    if not find_edges(plan, source=triage["id"], target=pending["id"]):
        sys.exit("FAIL: no edge Triage → Pending Path")

    outbound_from_triage = find_edges(plan, source=triage["id"])
    if len(outbound_from_triage) < 3:
        sys.exit(
            f"FAIL: Triage wide fan-out should have ≥3 outbound edges; "
            f"got {len(outbound_from_triage)}"
        )

    labels = {lbl.lower() for lbl in edge_labels_from(plan, triage["id"])}
    if not {"approved", "rejected", "pending"}.issubset(labels):
        sys.exit(
            f"FAIL: outbound edges from Triage missing Approved/Rejected/Pending labels; "
            f"got {sorted(labels)}"
        )

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
            f"(closes the exit-only + wait-for-connector + marks-complete:true cell); "
            f"got {pending_exit.get('marksStageComplete')!r}"
        )
    pending_rule = first_rule_of_condition(pending_exit)
    if not pending_rule or pending_rule.get("rule") != "wait-for-connector":
        sys.exit(
            f"FAIL: Triage→Pending exit rule should be 'wait-for-connector'; "
            f"got {pending_rule and pending_rule.get('rule')!r}"
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

    rejected_edges = find_edges(plan, source=triage["id"], target=rejected["id"])
    rejected_edge = rejected_edges[0]
    src_handle = rejected_edge.get("sourceHandle") or ""
    tgt_handle = rejected_edge.get("targetHandle") or ""
    if not src_handle.endswith("____bottom"):
        sys.exit(
            f"FAIL: Triage→Rejected Path edge sourceHandle should end with "
            f"'____bottom' (custom override); got {src_handle!r}"
        )
    if not tgt_handle.endswith("____top"):
        sys.exit(
            f"FAIL: Triage→Rejected Path edge targetHandle should end with "
            f"'____top' (custom override); got {tgt_handle!r}"
        )

    print(
        "OK: Triage WIDE fan-outs to Approved/Rejected/Pending (3 branches); exits "
        "cover wait-for-user + exit-only(marks-complete:false) + exit-only(marks-"
        "complete:TRUE on Pending wait-for-connector); Approved Path has "
        "user-selected-stage entry; all three edge labels present; Triage→Rejected "
        "uses custom handles (bottom→top)"
    )


if __name__ == "__main__":
    main()
