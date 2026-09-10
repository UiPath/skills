#!/usr/bin/env python3
"""Assert the approval-chain mechanisms survive adaptation to a near-miss shape.

Grades only what the pattern guide calls load-bearing, never the stock shape.
An agent that adds a fourth approver, renames nodes, or lays the diagram out
differently still passes; an agent that force-fits the request into a purely
sequential or purely parallel chain, or that collapses the per-approver audit
trail onto one shared variable, does not.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from bpmn_assertions import (  # noqa: E402
    BPMN_NS,
    elements,
    fail,
    load_bpmn,
)
from graph import ids, reachable, reaches  # noqa: E402

BPMN = "VendorOnboarding/VendorOnboarding.bpmn"
OUTCOME_RE = re.compile(r"vars\.([A-Za-z_][A-Za-z0-9_]*)")


def main() -> None:
    root = load_bpmn(BPMN)

    user_tasks = elements(root, "userTask")
    if len(user_tasks) < 3:
        fail(f"expected a review task per approver (3), found {len(user_tasks)}")

    # Adapted, not force-fitted: the two concurrent reviewers need a parallel
    # split and merge, which neither stock variant of the pattern has alongside
    # a following sequential step.
    parallel = elements(root, "parallelGateway")
    if len(parallel) < 2:
        fail(
            "expected a parallel gateway pair for the two concurrent reviewers, "
            f"found {len(parallel)} — the shape was not adapted"
        )

    # Counting gateways is not the adaptation. A fork must reach at least two
    # review tasks, and a third review must sit downstream of the join — three
    # sequential reviews beside two detached gateways is the shape this rejects.
    task_ids = ids(user_tasks)
    forks = [
        g for g in parallel
        if len(reachable(root, g.attrib.get("id", "")) & task_ids) >= 2
    ]
    if not forks:
        fail("no parallel gateway reaches two review tasks — the concurrent pair was not modelled")

    joins = [
        g for g in parallel
        if g not in forks and any(reaches(root, t, g.attrib.get("id", "")) for t in task_ids)
    ]
    if not joins:
        fail("the concurrent reviews never merge on a parallel join")

    join_id = joins[0].attrib.get("id", "")
    if not (reachable(root, join_id) & task_ids):
        fail("no review task follows the join — the third approver does not act after the other two")

    # The chain can stop at any step: a decision gateway is what makes that
    # possible, and there must be more than the parallel merge.
    exclusive = elements(root, "exclusiveGateway")
    if len(exclusive) < 2:
        fail(f"expected at least 2 exclusive gateways for approve/reject decisions, found {len(exclusive)}")

    # Per-approver outcomes: conditions must read more than one distinct
    # variable, or the last approver has overwritten everyone else's verdict.
    conditions = [
        (c.text or "")
        for c in root.findall(f".//{{{BPMN_NS}}}conditionExpression")
    ]
    if not conditions:
        fail("no conditionExpression found — nothing gates the chain")
    referenced = {v for c in conditions for v in OUTCOME_RE.findall(c)}
    if len(referenced) < 2:
        fail(
            "gateway conditions read fewer than two distinct variables "
            f"({sorted(referenced) or 'none'}) — per-approver outcomes were collapsed"
        )

    # Rejection is a documented exit, distinct from the fulfilled one.
    end_events = elements(root, "endEvent")
    if len(end_events) < 2:
        fail(f"expected separate fulfilled and rejected end events, found {len(end_events)}")

    # Diagram is mandatory for import.
    if not root.findall(".//{http://www.omg.org/spec/BPMN/20100524/DI}BPMNDiagram"):
        fail("no bpmndi:BPMNDiagram — the file will not import")

    print(
        f"PASS: {len(user_tasks)} review tasks, {len(parallel)} parallel gateways, "
        f"{len(exclusive)} exclusive gateways, {len(referenced)} distinct outcome variables, "
        f"{len(end_events)} named exits"
    )


if __name__ == "__main__":
    main()
