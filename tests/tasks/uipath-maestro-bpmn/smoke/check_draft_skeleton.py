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


def wiring_payloads(root) -> list:
    """Every uipath:activity payload except an error boundary's capture.

    A decision that routes on the error code reads it from a variable, and the
    builder SDK's onError({ errorVar }) writes that capture on the boundary as
    a bare uipath:Activity payload holding one `=Error` output row and nothing
    else. That is not wiring; any other payload, anywhere, is.
    """
    parents = {child: parent for parent in root.iter() for child in parent}
    wiring = []
    for act in root.iter(f"{{{NS['uipath']}}}activity"):
        ext = parents.get(act)
        owner = parents.get(ext) if ext is not None else None
        kids = list(act)
        types = [k for k in kids if k.tag == f"{{{NS['uipath']}}}type"]
        outputs = [k for k in kids if k.tag == f"{{{NS['uipath']}}}output"]
        capture = (
            ext is not None and ext.tag == f"{{{NS['bpmn']}}}extensionElements"
            and owner is not None and owner.tag == f"{{{NS['bpmn']}}}boundaryEvent"
            and owner.find("bpmn:errorEventDefinition", NS) is not None
            and len(kids) == 2 and len(types) == 1 and len(outputs) == 1
            and attr(types[0], "value") == "uipath:Activity"
            and attr(outputs[0], "name") == "Error" and attr(outputs[0], "source") == "=Error"
            and len(outputs[0]) == 0
        )
        if not capture:
            wiring.append(act)
    return wiring


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

    A parallel join waits for one token on each of its incoming flows. Each
    branch the fork opens is checked on its own:

    - A plain end event the branch can reach, by sequence flow or through an
      interrupting boundary, swallows the branch's token. Terminate and error
      end events end the instance, so they are safe.
    - An interrupting boundary path must merge back onto its own branch: if it
      reaches the join through a sibling branch or as an extra join input, the
      branch's own join input never delivers.
    - A non-interrupting boundary path adds a token while the branch's own
      token still reaches the join, so it may end separately, but it must not
      add a join input that only delivers when it fires.

    Nested fork/join pairs are tracked by depth.
    """
    succ: dict[str, list[str]] = {}
    incoming: dict[str, int] = {}
    for f in flows:
        succ.setdefault(attr(f, "sourceRef"), []).append(attr(f, "targetRef"))
        incoming[attr(f, "targetRef")] = incoming.get(attr(f, "targetRef"), 0) + 1
    interrupting: dict[str, list[str]] = {}
    non_interrupting: dict[str, list[str]] = {}
    for b in elements(root, "boundaryEvent"):
        kind = non_interrupting if attr(b, "cancelActivity") == "false" else interrupting
        kind.setdefault(attr(b, "attachedToRef"), []).append(attr(b, "id"))
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

    def walk(stack, with_boundaries: bool):
        seen: set[tuple[str, int]] = set()
        entries: set[str] = set()  # sources whose flow closes the walk at its join
        while stack:
            node, depth, src = stack.pop()
            if node in joins:
                depth -= 1
                if depth == 0:
                    entries.add(src)
                    continue
            if (node, depth) in seen:
                continue
            seen.add((node, depth))
            if node in fork_set:
                depth = min(depth + 1, cap)
            nxt = list(succ.get(node, []))
            if with_boundaries:
                nxt += interrupting.get(node, [])
            stack.extend((n, depth, node) for n in nxt)
        return seen, entries

    for fork in forks:
        branches = []
        for first in succ[fork]:
            normal, own = walk([(first, 1, fork)], False)
            branches.append((first, {n for n, _ in normal}, own))
        if not any(own for _, _, own in branches):
            continue
        for first, normal, own in branches:
            full, entries = walk([(first, 1, fork)], True)
            stuck = sorted({n for n, _ in full} & plain_ends)
            if stuck:
                fail(f"a path out of parallel fork {fork} stops at plain end event(s) {stuck} while the join "
                     "waits; end it with a terminate end event or merge it back onto its own branch")
            foreign = sorted(entries - own)
            if foreign:
                fail(f"an error or timer path on branch {first} of fork {fork} reaches the join through {foreign} "
                     "instead of its own branch, so its own join input never delivers; merge it onto its own "
                     "branch before the join")
            for node, depth in sorted(full):
                for b in non_interrupting.get(node, []):
                    _, extra = walk([(b, depth, node)], True)
                    added = sorted(extra - own)
                    if added:
                        fail(f"a non-interrupting path from {b} on fork {fork} feeds the join through {added}, "
                             "an input that only delivers when it fires; end it separately or merge it onto "
                             "its own branch")


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
    if wiring_payloads(root):
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
