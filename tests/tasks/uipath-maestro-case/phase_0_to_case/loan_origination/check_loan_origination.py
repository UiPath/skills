#!/usr/bin/env python3
"""LoanOrigination Phase 0 → case generation: logical-integrity grader.

Checks that the agent-generated caseplan.json from the Accrual Capital
commercial-loan-origination narrative encodes a workable process, not
just a structurally valid one:

  - 6 primary stages exist with the expected names
  - Gating chain Intake → Loan Setup → Underwriting → QA/QC → Closing → Resolved
    exists as a condition-driven transition path (edges retired; arbitrary
    intermediate routing allowed)
  - At least 3 of the 4 named exception lanes (Customer Comms, Escalation,
    Withdrawn, Rejected) exist as ExceptionStage nodes OR as regular stages
  - Withdrawn and Rejected are terminal (no outgoing transitions leaving them
    back into the happy path) and at least one terminal exception drives a
    case-exit condition that marks the case complete
  - Resolved is required and terminal
  - At least one conditional rule references the >$5M Credit-Analyst gate
  - Total task count is realistic (≥ 25)
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
    find_transitions,
    find_stages,
    first_rule_of_condition,
    get_case_exit_conditions,
    iter_stage_entry_conditions,
    iter_stage_exit_conditions,
    iter_tasks,
    read_caseplan,
)


PRIMARY_STAGES = [
    "Intake",
    "Loan Setup",
    "Underwriting",
    "QA/QC",
    "Closing",
    "Resolved",
]
EXCEPTION_STAGES = ["Customer Comms", "Escalation", "Withdrawn", "Rejected"]


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
    all_stages = find_stages(plan, include_exception=True)
    if not all_stages:
        _fail("no stages found in caseplan")
    stage_labels = [_label(s) for s in all_stages]

    # 1. Primary stages exist
    primary_nodes: dict[str, dict] = {}
    missing = []
    for name in PRIMARY_STAGES:
        node = _find_stage_by_name(all_stages, name)
        if not node:
            missing.append(name)
        else:
            primary_nodes[name] = node
    if missing:
        _fail(
            f"missing primary stage(s) {missing}; stages present: {stage_labels}"
        )

    # 2. Gating chain — must reach Resolved from Intake; happy-path order must
    #    be respected at least pairwise for the consecutive primary stages.
    for src, dst in zip(PRIMARY_STAGES, PRIMARY_STAGES[1:]):
        s_id = primary_nodes[src]["id"]
        d_id = primary_nodes[dst]["id"]
        if not _has_path(plan, s_id, d_id):
            _fail(
                f"no transition path from {src!r} to {dst!r}; gating chain broken "
                f"between consecutive primary stages"
            )

    # 3. Exception lanes — at least 3 of 4 present (some skills collapse
    #    Customer Comms into a comms loop without modeling it as a stage).
    found_exceptions = [
        name for name in EXCEPTION_STAGES if _find_stage_by_name(all_stages, name)
    ]
    if len(found_exceptions) < 3:
        _fail(
            f"need ≥3 of {EXCEPTION_STAGES} as stages; got {found_exceptions}. "
            f"All stage labels: {stage_labels}"
        )

    # 4. Withdrawn / Rejected terminality — no outgoing transitions back into a
    #    non-exception stage (terminal lane).
    primary_ids = {n["id"] for n in primary_nodes.values()}
    for name in ("Withdrawn", "Rejected"):
        node = _find_stage_by_name(all_stages, name)
        if not node:
            continue  # already covered by exception count
        bad = []
        for tr in find_transitions(plan, source=node["id"]):
            tgt = tr.get("target")
            if tgt in primary_ids and tgt != node["id"]:
                bad.append(tgt)
        if bad:
            _fail(
                f"terminal exception {name!r} should not route back to a "
                f"primary stage; found transitions to {bad}"
            )

    # 5. Resolved required + terminal
    resolved = primary_nodes["Resolved"]
    if (resolved.get("data") or {}).get("isRequired") is False:
        _fail(
            "Resolved stage should be required for case completion "
            "(isRequired=true); got isRequired=false"
        )
    out_transitions = find_transitions(plan, source=resolved["id"])
    if out_transitions:
        # Allow exit-to into an exception stage but not into another primary
        leaks = [
            t.get("target")
            for t in out_transitions
            if t.get("target") in primary_ids and t.get("target") != resolved["id"]
        ]
        if leaks:
            _fail(
                f"Resolved stage should be terminal; has outgoing transitions to "
                f"{leaks}"
            )

    # 6. Case-exit conditions cover happy path + at least one terminal
    #    exception. required-stages-completed must mark the case complete.
    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) < 2:
        _fail(
            f"expected ≥2 case-exit conditions (happy + ≥1 terminal "
            f"exception); got {len(case_exits)}"
        )
    happy_found = False
    terminal_found = False
    terminal_ids = {
        primary_nodes["Resolved"]["id"],
        *(
            _find_stage_by_name(all_stages, n)["id"]
            for n in ("Withdrawn", "Rejected")
            if _find_stage_by_name(all_stages, n)
        ),
    }
    for ce in case_exits:
        rule = first_rule_of_condition(ce) or {}
        rname = rule.get("rule")
        marks = ce.get("marksCaseComplete")
        if rname == "required-stages-completed" and marks is True:
            happy_found = True
        # Terminal exceptions (Withdrawn / Rejected) close the case via a
        # selected-stage-* case-exit with marksCaseComplete=FALSE — the
        # platform-mandated shape: selected-stage-* may pair ONLY with
        # marks-case-complete=false (marks=true is reserved for
        # required-stages-completed). So accept the rule regardless of `marks`.
        if (
            rname in ("selected-stage-completed", "selected-stage-exited")
            and rule.get("selectedStageId") in terminal_ids
        ):
            terminal_found = True
    if not happy_found:
        _fail(
            "missing case-exit 'required-stages-completed' with "
            "marksCaseComplete=true (happy-path closure)"
        )
    if not terminal_found:
        _fail(
            "no case-exit references a terminal exception (Withdrawn / Rejected "
            "/ Resolved) via selected-stage-completed/-exited; a terminal lane "
            "must drive a case-exit condition (marks-case-complete=false)"
        )

    # 7. Conditional gating: somewhere in the plan we expect a rule
    #    referencing the >$5M Credit-Analyst threshold.
    plan_text = repr(plan).lower()
    if not re.search(r"5[\s_]*0{0,3}[\s_]*0{3}", plan_text) and "5m" not in plan_text:
        _fail(
            "no expression referencing the $5M Credit-Analyst threshold "
            "found anywhere in caseplan (expected a conditional rule "
            "gating Credit-Analyst tasks on loanAmount > 5M)"
        )

    # 8. Task volume sanity check
    task_count = sum(1 for _ in iter_tasks(plan))
    if task_count < 25:
        _fail(
            f"task volume too low: got {task_count}, expected ≥25 for a "
            f"~45-task commercial-loan-origination process"
        )

    print(
        f"OK: {len(primary_nodes)} primary stages in chain; "
        f"{len(found_exceptions)} exception lanes ({found_exceptions}); "
        f"happy-path + terminal-exception case-exits present; "
        f"{task_count} tasks total"
    )


if __name__ == "__main__":
    main()
