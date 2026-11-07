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
    """One sequential multi-instance box that stops early, one parallel one."""
    seq_stop = par = False
    for mi in root.iter(f"{{{NS['bpmn']}}}multiInstanceLoopCharacteristics"):
        loop = mi.find("bpmn:extensionElements/uipath:loopCharacteristics", NS)
        if loop is None or not attr(loop, "inputCollection"):
            fail("a multi-instance marker has no uipath:loopCharacteristics inputCollection")
        if attr(mi, "isSequential") == "true":
            cond = mi.find("bpmn:completionCondition", NS)
            seq_stop |= cond is not None and bool((cond.text or "").strip())
        else:
            par = True
    if not seq_stop:
        fail("expected a sequential multi-instance box with a completionCondition (stop at the first out-of-stock item)")
    if not par:
        fail("expected a parallel multi-instance box (notify every supplier at once)")


def require_fork_exits_safe(root, flows) -> None:
    """No path out of a joined parallel fork may stop at a plain end event.

    A parallel join waits for every branch it forked, so a branch that leaves
    for a plain end event leaves the instance running forever. Walk each fork's
    branches, following error and timer boundaries, up to the join.
    """
    succ: dict[str, list[str]] = {}
    incoming: dict[str, int] = {}
    for f in flows:
        succ.setdefault(attr(f, "sourceRef"), []).append(attr(f, "targetRef"))
        incoming[attr(f, "targetRef")] = incoming.get(attr(f, "targetRef"), 0) + 1
    for b in elements(root, "boundaryEvent"):
        succ.setdefault(attr(b, "attachedToRef"), []).append(attr(b, "id"))
    parallels = elements(root, "parallelGateway")
    joins = {attr(g, "id") for g in parallels if incoming.get(attr(g, "id"), 0) > 1}
    forks = [attr(g, "id") for g in parallels if len(succ.get(attr(g, "id"), [])) > 1]
    if not forks or not joins:
        fail("expected a parallel fork and join (the packing steps run in parallel)")
    plain_ends = {
        attr(e, "id") for e in elements(root, "endEvent")
        if e.find("bpmn:terminateEventDefinition", NS) is None
    }
    for fork in forks:
        seen: set[str] = set()
        stack = list(succ[fork])
        reached_join = False
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in joins:
                reached_join = True
                continue
            stack.extend(succ.get(node, []))
        stuck = sorted(seen & plain_ends)
        if reached_join and stuck:
            fail(f"a path out of parallel fork {fork} stops at plain end event(s) {stuck} while the join "
                 "waits; end it with a terminate end event or route it back into the join")


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
        # An inclusive gateway ("picking, packing, or both") may condition
        # every branch with no default; an exclusive one needs its default.
        exclusive = elements(root, "exclusiveGateway")
        inclusive = elements(root, "inclusiveGateway")
        if not exclusive and not inclusive:
            fail("missing a bpmn:exclusiveGateway or bpmn:inclusiveGateway")
        if not inclusive and not any(attr(g, "default") for g in exclusive):
            fail("exclusive gateway is missing a default sequence-flow reference")
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
