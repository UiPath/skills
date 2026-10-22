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
from graph import edges, ids, parent_map, reachable, reaches  # noqa: E402

BPMN = "VendorOnboarding/VendorOnboarding.bpmn"
OUTCOME_RE = re.compile(r"vars\.([A-Za-z_][A-Za-z0-9_]*)")
SIDE_EFFECT_KINDS = ("serviceTask", "sendTask")
ERROR_DEF = f"{{{BPMN_NS}}}errorEventDefinition"
TERMINATE_DEF = f"{{{BPMN_NS}}}terminateEventDefinition"


def gates_stage(
    root, join_id: str, gate_id: str, review_id: str, reviews: set[str], end_ids: set[str]
) -> bool:
    if gate_id not in reachable(root, join_id):
        return False
    if review_id in reachable(root, join_id, blocked={gate_id}):
        return False
    return bool(reachable(root, gate_id, blocked=reviews) & end_ids)


def catches(definition, error_ref: str | None) -> bool:
    handled = definition.attrib.get("errorRef")
    return not handled or handled == error_ref


def error_caught(root, end, parents, later: set[str]) -> bool:
    error_ref = end.find(ERROR_DEF).attrib.get("errorRef")
    scopes = []
    node = end
    while node in parents:
        node = parents[node]
        scopes.append(node)

    for sub in elements(root, "subProcess"):
        if sub.attrib.get("triggeredByEvent") != "true" or sub in scopes or parents.get(sub) not in scopes:
            continue
        for start in sub.findall(f"{{{BPMN_NS}}}startEvent"):
            definition = start.find(ERROR_DEF)
            if definition is None or start.attrib.get("isInterrupting") == "false":
                continue
            if catches(definition, error_ref):
                return True

    scope_ids = ids(scopes)
    for boundary in elements(root, "boundaryEvent"):
        definition = boundary.find(ERROR_DEF)
        if definition is None or boundary.attrib.get("attachedToRef") not in scope_ids:
            continue
        if boundary.attrib.get("cancelActivity") == "false" or not catches(definition, error_ref):
            continue
        if not reachable(root, boundary.attrib.get("id", "")) & later:
            return True
    return False


def stopping_ends(root, later: set[str]) -> set[str]:
    # A plain end in one parallel branch leaves the join waiting on the other,
    # and an uncaught error end faults the instance instead of rejecting it.
    parents = parent_map(root)
    stopping = set()
    for end in elements(root, "endEvent"):
        if end.find(TERMINATE_DEF) is not None:
            stopping.add(end.attrib.get("id", ""))
        elif end.find(ERROR_DEF) is not None and error_caught(root, end, parents, later):
            stopping.add(end.attrib.get("id", ""))
    return stopping


def rejects_before_join(
    root, review_id: str, join_id: str, gate_ids: set[str], task_ids: set[str], later: set[str], stop_ids: set[str]
) -> bool:
    if join_id in reachable(root, review_id, blocked=gate_ids):
        return False
    end_ids = ids(elements(root, "endEvent"))
    for gate_id in verdict_gates(root, review_id, gate_ids, task_ids):
        for source, exit_id in edges(root):
            if source != gate_id:
                continue
            after = {exit_id} | reachable(root, exit_id)
            ends = after & end_ids
            if join_id not in after and not after & later and ends and ends <= stop_ids:
                return True
    return False


def gated_before_join(
    root, fork_id: str, join_id: str, gate_ids: set[str], task_ids: set[str], later: set[str]
) -> bool:
    branch = {t for t in reachable(root, fork_id, blocked={join_id}) & task_ids if reaches(root, t, join_id)}
    if not branch:
        return False
    stop_ids = stopping_ends(root, later)
    return all(rejects_before_join(root, r, join_id, gate_ids, task_ids, later, stop_ids) for r in branch)


def verdict_gates(root, review_id: str, gate_ids: set[str], reviews: set[str]) -> set[str]:
    blocked = gate_ids | (reviews - {review_id})
    before_gate = {review_id} | reachable(root, review_id, blocked=blocked)
    return {target for source, target in edges(root) if source in before_gate and target in gate_ids}


def terminates(root, node_id: str, blocked: set[str], end_ids: set[str]) -> bool:
    if node_id in blocked:
        return False
    return node_id in end_ids or bool(reachable(root, node_id, blocked=blocked) & end_ids)


def can_reject(root, gate_id: str, end_ids: set[str], side_effect_ids: set[str]) -> bool:
    # Two exits that each finish without re-entering the gate, one of them
    # skipping every side effect of the other: a rejection that loops forever
    # or merges back into fulfillment is no exit.
    exits = {target for source, target in edges(root) if source == gate_id}
    for kept in exits:
        if not terminates(root, kept, {gate_id}, end_ids):
            continue
        fulfilled = ({kept} | reachable(root, kept, blocked={gate_id})) & side_effect_ids
        if any(terminates(root, other, {gate_id} | fulfilled, end_ids) for other in exits - {kept}):
            return True
    return False


def out_degree(root, node_id: str) -> int:
    return sum(1 for source, _target in edges(root) if source == node_id)


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
        if out_degree(root, g.attrib.get("id", "")) >= 2
        and len(reachable(root, g.attrib.get("id", "")) & task_ids) >= 2
    ]
    if not forks:
        fail("no parallel gateway reaches two review tasks — the concurrent pair was not modelled")

    joins = [
        g for g in parallel
        if out_degree(root, g.attrib.get("id", "")) < 2
        and any(reaches(root, t, g.attrib.get("id", "")) for t in task_ids)
    ]
    if not joins:
        fail("the concurrent reviews never merge on a parallel join")

    join_id = joins[0].attrib.get("id", "")
    sequential = reachable(root, join_id) & task_ids
    if not sequential:
        fail("no review task follows the join — the third approver does not act after the other two")

    # The chain can stop at any step: between the join and each later review,
    # an exclusive gateway must be able to exit to an end without any later review,
    # or every parallel review is gated before the join on an exit that stops the instance.
    exclusive = elements(root, "exclusiveGateway")
    gate_ids = ids(exclusive)
    end_ids = ids(elements(root, "endEvent"))
    side_effect_ids = ids([e for kind in SIDE_EFFECT_KINDS for e in elements(root, kind)])
    fork_id = forks[0].attrib.get("id", "")
    pre_join = gated_before_join(root, fork_id, join_id, gate_ids, task_ids, sequential)
    for review_id in sorted(sequential):
        if not pre_join and not any(gates_stage(root, join_id, g, review_id, sequential, end_ids) for g in gate_ids):
            fail(
                f"{review_id} is reachable from {join_id} without an exclusive gateway "
                "that can exit to an end past every later review, or a gate on each parallel review before "
                f"{join_id} whose reject exit ends only at terminate ends or caught error ends, "
                "so a parallel rejection still reaches it or leaves the join waiting"
            )

        # And each later review's own verdict is gated before the process can end.
        if reachable(root, review_id, blocked=gate_ids) & end_ids:
            fail(f"{review_id} reaches an end without an exclusive gateway, so its rejection cannot stop the chain")
        verdicts = verdict_gates(root, review_id, gate_ids, sequential)
        if not any(can_reject(root, g, end_ids, side_effect_ids) for g in verdicts):
            fail(f"no exclusive gateway after {review_id} offers a second route to an end, so its rejection has no exit")
        acted_before_verdict = reachable(root, review_id, blocked=gate_ids) & side_effect_ids
        if acted_before_verdict:
            fail(f"{sorted(acted_before_verdict)} run after {review_id} before its verdict gateway, so a rejection lands too late")

        only_via_review = reachable(root, review_id) - reachable(root, join_id, blocked={review_id})
        if not (only_via_review & end_ids):
            fail(f"every end is reachable from {join_id} without {review_id}, so the process can finish without its approval")

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
