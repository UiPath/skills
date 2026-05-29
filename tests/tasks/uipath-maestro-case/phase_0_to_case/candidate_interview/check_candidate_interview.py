#!/usr/bin/env python3
"""CandidateInterview Phase 0 → case generation: logical-integrity grader.

Checks that the generated caseplan.json encodes a workable hiring process:

  - 7 primary stages exist with the expected names
  - Gating chain Application Received → Recruiter Screen → Technical Screen
    → Onsite Loop → Debrief → Offer → Hired exists as an edge path
  - At least 2 of the 3 named exception lanes (Rejected, Withdrawn, On Hold)
    exist as stages
  - Hired is required and terminal (no edges back to a primary stage)
  - Rejected / Withdrawn terminal lanes do not leak back into the happy path
  - Case-exit conditions cover happy-path closure (required-stages-completed
    or selected-stage-completed on Hired) AND ≥1 terminal exception
  - Some rule references the L4+ / engineering-role onsite gating
  - Some condition references the debrief-after-scorecard precondition
  - Realistic task volume (≥ 18)
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.case_check import (  # noqa: E402
    find_edges,
    find_stages,
    first_rule_of_condition,
    get_case_exit_conditions,
    iter_tasks,
    read_caseplan,
)


PRIMARY_STAGES = [
    "Application Received",
    "Recruiter Screen",
    "Technical Screen",
    "Onsite Loop",
    "Debrief",
    "Offer",
    "Hired",
]
EXCEPTION_STAGES = ["Rejected", "Withdrawn", "On Hold"]


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
            for edge in find_edges(plan, source=node_id):
                t = edge.get("target")
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
    all_stages = find_stages(plan, include_exception=True)
    if not all_stages:
        _fail("no stages found in caseplan")
    stage_labels = [_label(s) for s in all_stages]

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

    for src, dst in zip(PRIMARY_STAGES, PRIMARY_STAGES[1:]):
        s_id = primary_nodes[src]["id"]
        d_id = primary_nodes[dst]["id"]
        if not _has_path(plan, s_id, d_id):
            _fail(
                f"no edge path from {src!r} to {dst!r}; gating chain broken"
            )

    found_exceptions = [
        name for name in EXCEPTION_STAGES if _find_stage_by_name(all_stages, name)
    ]
    if len(found_exceptions) < 2:
        _fail(
            f"need ≥2 of {EXCEPTION_STAGES} as stages; got {found_exceptions}. "
            f"All stage labels: {stage_labels}"
        )

    primary_ids = {n["id"] for n in primary_nodes.values()}
    for name in ("Rejected", "Withdrawn"):
        node = _find_stage_by_name(all_stages, name)
        if not node:
            continue
        bad = [
            e.get("target")
            for e in find_edges(plan, source=node["id"])
            if e.get("target") in primary_ids and e.get("target") != node["id"]
        ]
        if bad:
            _fail(
                f"terminal exception {name!r} should not route back into the "
                f"primary chain; edges to {bad}"
            )

    hired = primary_nodes["Hired"]
    if (hired.get("data") or {}).get("isRequired") is False:
        _fail("Hired should be required for case completion; got isRequired=false")
    leaks = [
        e.get("target")
        for e in find_edges(plan, source=hired["id"])
        if e.get("target") in primary_ids and e.get("target") != hired["id"]
    ]
    if leaks:
        _fail(f"Hired should be terminal; outgoing edges to {leaks}")

    case_exits = get_case_exit_conditions(plan)
    if len(case_exits) < 2:
        _fail(
            f"expected ≥2 case-exit conditions; got {len(case_exits)}"
        )
    happy = False
    terminal = False
    terminal_ids = {hired["id"]}
    for name in ("Rejected", "Withdrawn"):
        node = _find_stage_by_name(all_stages, name)
        if node:
            terminal_ids.add(node["id"])
    for ce in case_exits:
        rule = first_rule_of_condition(ce) or {}
        rname = rule.get("rule")
        marks = ce.get("marksCaseComplete")
        if rname == "required-stages-completed" and marks is True:
            happy = True
        if (
            rname in ("selected-stage-completed", "selected-stage-exited")
            and marks is True
            and rule.get("selectedStageId") in terminal_ids
        ):
            terminal = True
    if not happy:
        _fail(
            "missing happy-path case-exit ('required-stages-completed', "
            "marksCaseComplete=true)"
        )
    if not terminal:
        _fail(
            "no case-exit ties a terminal lane (Hired / Rejected / Withdrawn) "
            "to marksCaseComplete=true"
        )

    plan_text = repr(plan).lower()
    if not re.search(r"\bl[45]\b|engineer", plan_text):
        _fail(
            "no rule references the L4+ / engineering-role gating for the "
            "Onsite Loop"
        )
    if not re.search(r"scorecard|debrief|onsite.*complete", plan_text):
        _fail(
            "no rule references the debrief-after-scorecard / onsite-complete "
            "precondition"
        )

    task_count = sum(1 for _ in iter_tasks(plan))
    if task_count < 18:
        _fail(
            f"task volume too low: got {task_count}, expected ≥18 for a "
            f"~30-task hiring process"
        )

    print(
        f"OK: {len(primary_nodes)} primary stages chained; "
        f"{len(found_exceptions)} exception lanes ({found_exceptions}); "
        f"happy + terminal case-exits present; {task_count} tasks total"
    )


if __name__ == "__main__":
    main()
