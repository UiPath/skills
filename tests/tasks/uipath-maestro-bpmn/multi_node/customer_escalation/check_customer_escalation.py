#!/usr/bin/env python3
"""Structural check for the customer_escalation BPMN e2e port.

Enforces the ported intent: two classifier script tasks feed an exclusive
gateway whose high-touch branch is a human user task and whose default branch is
a ticket-generating script task, plus complete, consistent package metadata.
Grades authored XML/JSON shape, not runtime output.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

PROJECT = Path.cwd() / "CustomerEscalation"
BPMN_NAME = "CustomerEscalation.bpmn"
REQUIRED_FILES = [
    "project.uiproj",
    "bindings_v2.json",
    "entry-points.json",
    "operate.json",
    "package-descriptor.json",
]


def load_json(name: str):
    p = PROJECT / name
    if not p.is_file():
        fail(f"{name} is missing")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{name} is not valid JSON: {exc}")


def main() -> None:
    for name in REQUIRED_FILES:
        if not (PROJECT / name).is_file():
            fail(f"{name} is missing")

    path, root = parse_bpmn("CustomerEscalation")

    process = one_or_more(root, "process")[0]
    if process.attrib.get("isExecutable") != "true":
        fail("BPMN process must be executable")

    scripts = elements(root, "scriptTask")
    if len(scripts) < 3:
        fail(f"expected at least 3 script tasks (2 classifiers + ticket), found {len(scripts)}")

    if not elements(root, "userTask"):
        fail("no user task authored for the escalation path")

    gateways = one_or_more(root, "exclusiveGateway")
    flows = elements(root, "sequenceFlow")
    routed = False
    for gw in gateways:
        gw_id = attr(gw, "id")
        outgoing = [f for f in flows if attr(f, "sourceRef") == gw_id]
        if len(outgoing) < 2:
            continue
        default_id = attr(gw, "default")
        if not default_id:
            fail(f"exclusive gateway {gw_id} has no default flow")
        conditioned = [
            f for f in outgoing
            if attr(f, "id") != default_id and f.find("bpmn:conditionExpression", NS) is not None
        ]
        if not conditioned:
            fail(f"exclusive gateway {gw_id} has no conditioned branch")
        routed = True
    if not routed:
        fail("no exclusive gateway routing the combined escalation signal")

    if len(elements(root, "endEvent")) < 2:
        fail("expected an end event per escalation path")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)

    # Package metadata references the BPMN file.
    for name in ("entry-points.json", "operate.json", "package-descriptor.json"):
        if BPMN_NAME not in json.dumps(load_json(name)):
            fail(f"{name} must reference {BPMN_NAME}")

    print(f"OK: {path} classifies, routes, escalates via a user task, and ships consistent package metadata")


if __name__ == "__main__":
    main()
