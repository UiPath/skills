#!/usr/bin/env python3
"""Grade a draft-mode skeleton: bare task boxes, real control flow, no wiring.

Usage: check_draft_skeleton.py <ProjectName> [--timer-start]
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


def main() -> None:
    name = sys.argv[1]
    path, root = parse_bpmn(name)

    boxes = one_or_more(root, "task")
    if len(boxes) < 3:
        fail(f"expected at least 3 bare bpmn:task boxes in {path}, found {len(boxes)}")
    for tag in TYPED_ACTIVITIES:
        if root.findall(f".//bpmn:{tag}", NS):
            fail(f"skeleton contains a typed bpmn:{tag}; draft mode must stop before wiring")
    if root.findall(".//uipath:activity", NS):
        fail("skeleton contains a uipath:activity payload; draft mode must stop before wiring")

    gateways = one_or_more(root, "exclusiveGateway")
    if not any(attr(g, "default") for g in gateways):
        fail("exclusive gateway is missing a default sequence-flow reference")
    flows = one_or_more(root, "sequenceFlow")
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

    uip = shutil.which("uip")
    if not uip:
        fail("uip not found on PATH; cannot validate the skeleton")
    if uip:
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
