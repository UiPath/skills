#!/usr/bin/env python3
"""Grade a draft-mode skeleton: bare task boxes, real control flow, no wiring.

Usage: check_draft_skeleton.py <ProjectName> [--timer-start] [--multi-instance] [--fork-exits-safe]
"""

import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

# Typed activities a skeleton must not contain: phase 2 boxes are bare
# bpmn:task elements until the user approves the shape.
TYPED_ACTIVITIES = ("serviceTask", "sendTask", "receiveTask", "scriptTask", "userTask",
                    "businessRuleTask", "manualTask", "callActivity")


def require_multi_instance(root) -> None:
    """One sequential multi-instance box that stops early, one parallel one.

    A sequential box stops early through a completionCondition or through an
    interrupting error boundary on the box itself.
    """
    stoppers = {
        attr(b, "attachedToRef") for b in elements(root, "boundaryEvent")
        if b.find("bpmn:errorEventDefinition", NS) is not None and attr(b, "cancelActivity") != "false"
    }
    seq_stop = par = False
    for act in root.iter():
        mi = act.find("bpmn:multiInstanceLoopCharacteristics", NS)
        if mi is None:
            continue
        loop = mi.find("bpmn:extensionElements/uipath:loopCharacteristics", NS)
        if loop is None or not attr(loop, "inputCollection"):
            fail("a multi-instance marker has no uipath:loopCharacteristics inputCollection")
        if attr(mi, "isSequential") == "true":
            cond = mi.find("bpmn:completionCondition", NS)
            seq_stop |= (cond is not None and bool((cond.text or "").strip())) or attr(act, "id") in stoppers
        else:
            par = True
    if not seq_stop:
        fail("expected a sequential multi-instance box that stops early (a completionCondition or an error boundary)")
    if not par:
        fail("expected a parallel multi-instance box (one run per item, all at once)")


def require_fork_exits_safe(root, flows) -> None:
    """No path out of a joined parallel fork may stall its join.

    A parallel join waits for one token per branch its fork opened. A path
    that leaves a branch for a plain end event, or an interrupting error or
    timer path that flows straight into the join as an extra input, leaves
    the instance running forever. Terminate and error end events end the
    instance, so they are safe. Nested fork/join pairs are tracked by depth,
    so a plain end between an inner join and the outer join is caught.
    """
    succ: dict[str, list[str]] = {}
    incoming: dict[str, int] = {}
    for f in flows:
        succ.setdefault(attr(f, "sourceRef"), []).append(attr(f, "targetRef"))
        incoming[attr(f, "targetRef")] = incoming.get(attr(f, "targetRef"), 0) + 1
    # A non-interrupting boundary leaves its activity's token on the way to
    # the join, so it neither stalls nor feeds the join.
    boundary_succ: dict[str, list[str]] = {}
    for b in elements(root, "boundaryEvent"):
        if attr(b, "cancelActivity") == "false":
            continue
        boundary_succ.setdefault(attr(b, "attachedToRef"), []).append(attr(b, "id"))
    parallels = elements(root, "parallelGateway")
    joins = {attr(g, "id") for g in parallels if incoming.get(attr(g, "id"), 0) > 1}
    forks = [attr(g, "id") for g in parallels if len(succ.get(attr(g, "id"), [])) > 1]
    if not forks or not joins:
        fail("expected a parallel fork and join (the packing steps run in parallel)")
    plain_ends = {
        attr(e, "id") for e in elements(root, "endEvent")
        if e.find("bpmn:terminateEventDefinition", NS) is None
        and e.find("bpmn:errorEventDefinition", NS) is None
    }
    fork_set = set(forks)
    cap = len(forks) + 1

    def walk(fork: str, with_boundaries: bool):
        seen: set[tuple[str, int]] = set()
        nodes: set[str] = set()
        entries: set[tuple[str, str]] = set()  # (source, join) where the walk closes
        stack = [(n, 1, fork) for n in succ[fork]]
        while stack:
            node, depth, src = stack.pop()
            if node in joins:
                depth -= 1
                if depth == 0:
                    entries.add((src, node))
                    continue
            if (node, depth) in seen:
                continue
            seen.add((node, depth))
            nodes.add(node)
            if node in fork_set:
                depth = min(depth + 1, cap)
            nxt = list(succ.get(node, []))
            if with_boundaries:
                nxt += boundary_succ.get(node, [])
            stack.extend((n, depth, node) for n in nxt)
        return nodes, entries

    for fork in forks:
        normal, _ = walk(fork, False)
        full, entries = walk(fork, True)
        if not entries:
            continue
        stuck = sorted(full & plain_ends)
        if stuck:
            fail(f"a path out of parallel fork {fork} stops at plain end event(s) {stuck} while the join "
                 "waits; end it with a terminate end event or merge it back onto its own branch")
        extra = sorted(src for src, _ in entries if src not in normal and src != fork)
        if extra:
            fail(f"an error or timer path from {extra} flows straight into the join of fork {fork}, which then "
                 "waits for an input that never comes; merge it onto its own branch before the join")


def main() -> None:
    name = sys.argv[1]
    path, root = parse_bpmn(name)

    boxes = one_or_more(root, "task")
    # Two per-item boxes are a whole multi-instance request; others need three.
    min_boxes = 2 if "--multi-instance" in sys.argv else 3
    if len(boxes) < min_boxes:
        fail(f"expected at least {min_boxes} bare bpmn:task boxes in {path}, found {len(boxes)}")
    for tag in TYPED_ACTIVITIES:
        if root.findall(f".//bpmn:{tag}", NS):
            fail(f"skeleton contains a typed bpmn:{tag}; draft mode must stop before wiring")
    if root.findall(".//uipath:activity", NS):
        fail("skeleton contains a uipath:activity payload; draft mode must stop before wiring")

    flows = one_or_more(root, "sequenceFlow")
    # A per-item shape needs no decision; every other shape routes on one.
    if "--multi-instance" not in sys.argv:
        # Only the fork-exits shape ("picking, packing, or both") may use an
        # inclusive gateway; every branching exclusive gateway needs a default.
        exclusive = elements(root, "exclusiveGateway")
        inclusive = elements(root, "inclusiveGateway") if "--fork-exits-safe" in sys.argv else []
        if not exclusive and not inclusive:
            fail("missing a bpmn:exclusiveGateway" + (" or bpmn:inclusiveGateway" if "--fork-exits-safe" in sys.argv else ""))
        out: dict[str, int] = {}
        for f in flows:
            out[attr(f, "sourceRef")] = out.get(attr(f, "sourceRef"), 0) + 1
        for g in exclusive:
            if out.get(attr(g, "id"), 0) > 1 and not attr(g, "default"):
                fail(f"exclusive gateway {attr(g, 'id')} branches without a default sequence flow")
        if not any(f.find("bpmn:conditionExpression", NS) is not None for f in flows):
            fail("no sequence flow carries a condition")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)

    if not os.path.isfile(os.path.join(os.path.dirname(path), "project.uiproj")):
        fail(f"project.uiproj missing beside {path}")

    if "--timer-start" in sys.argv:
        starts = one_or_more(root, "startEvent")
        if not any(s.find("bpmn:timerEventDefinition", NS) is not None for s in starts):
            fail("expected a timer start event (bpmn:timerEventDefinition on a startEvent)")

    if "--multi-instance" in sys.argv:
        require_multi_instance(root)
    if "--fork-exits-safe" in sys.argv:
        require_fork_exits_safe(root, flows)

    uip = shutil.which("uip")
    if not uip:
        fail("uip not found on PATH; cannot validate the skeleton")
    res = subprocess.run([uip, "maestro", "bpmn", "validate", path, "--output", "json"],
                         capture_output=True, text=True, timeout=45)
    try:
        data = json.loads(res.stdout).get("Data") or {}
    except ValueError:
        data = {}
    status = data.get("Status") or data.get("status")
    if status != "Valid":
        fail(f"uip maestro bpmn validate did not report Valid (exit {res.returncode}): {res.stdout[:400]}")

    print(f"OK: {path} is a validated draft skeleton with {len(boxes)} bare boxes and no wiring")


if __name__ == "__main__":
    main()
