#!/usr/bin/env python3
"""Structural check for the author-validate smoke task.

Verifies the agent authored a well-formed, importable Maestro BPMN: a diagram
shape for every node, an edge for every flow, resolvable sequence-flow refs, and
an exclusive gateway whose non-default branches carry conditions with exactly
one default. Reuses the shared uipath-maestro-bpmn check helpers (stdlib ET, same
trust boundary as the rest of the fixture corpus — input is locally authored,
not untrusted).
"""

from __future__ import annotations

import math
import os
import sys
import xml.etree.ElementTree as ET

# Import shared helpers from the task suite's _shared module.
_shared = (os.path.join(os.environ["SKILLS_REPO_PATH"],
                        "tests", "tasks", "uipath-maestro-bpmn", "_shared")
           if os.environ.get("SKILLS_REPO_PATH")
           else os.path.join(os.path.dirname(__file__), "..", "_shared"))
sys.path.insert(0, _shared)

from bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

DI_NS = {
    **NS,
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
}


def load_bpmn() -> tuple[str, ET.Element]:
    return parse_bpmn("InvoiceApproval")


def finite_number(value: str, label: str) -> float:
    try:
        number = float(value)
    except ValueError:
        fail(f"{label} is not numeric: {value!r}")
    if not math.isfinite(number):
        fail(f"{label} is not finite: {value!r}")
    return number


def require_complete_di_geometry(root: ET.Element) -> None:
    diagrams = root.findall(".//bpmndi:BPMNDiagram", DI_NS)
    if not diagrams:
        fail("missing BPMNDiagram")
    if not root.findall(".//bpmndi:BPMNPlane", DI_NS):
        fail("missing BPMNPlane")

    for shape in root.findall(".//bpmndi:BPMNShape", DI_NS):
        element_id = attr(shape, "bpmnElement") or attr(shape, "id")
        bounds = shape.find("dc:Bounds", DI_NS)
        if bounds is None:
            fail(f"BPMNShape {element_id} has no dc:Bounds")
        finite_number(attr(bounds, "x"), f"BPMNShape {element_id} x")
        finite_number(attr(bounds, "y"), f"BPMNShape {element_id} y")
        width = finite_number(attr(bounds, "width"), f"BPMNShape {element_id} width")
        height = finite_number(attr(bounds, "height"), f"BPMNShape {element_id} height")
        if width <= 0 or height <= 0:
            fail(f"BPMNShape {element_id} must have positive width and height")

    for edge in root.findall(".//bpmndi:BPMNEdge", DI_NS):
        element_id = attr(edge, "bpmnElement") or attr(edge, "id")
        waypoints = edge.findall("di:waypoint", DI_NS)
        if len(waypoints) < 2:
            fail(f"BPMNEdge {element_id} has fewer than two waypoints")
        for index, waypoint in enumerate(waypoints):
            finite_number(
                attr(waypoint, "x"),
                f"BPMNEdge {element_id} waypoint {index} x",
            )
            finite_number(
                attr(waypoint, "y"),
                f"BPMNEdge {element_id} waypoint {index} y",
            )


def main() -> None:
    _path, root = load_bpmn()

    if not elements(root, "startEvent"):
        fail("no start event")
    if not elements(root, "endEvent"):
        fail("no end event")

    gateways = elements(root, "exclusiveGateway")
    if not gateways:
        fail("no exclusive gateway authored")

    # Diagram + reference integrity (importable on the canvas).
    require_di_for_visible_elements(root)
    require_complete_di_geometry(root)
    require_sequence_integrity(root)

    # Exclusive-gateway routing: exactly one default; every other outgoing flow
    # carries a condition expression.
    flows_by_id = {attr(f, "id"): f for f in elements(root, "sequenceFlow")}
    for gw in gateways:
        gw_id = attr(gw, "id")
        outgoing = [f for f in flows_by_id.values() if attr(f, "sourceRef") == gw_id]
        if len(outgoing) < 2:
            fail(f"exclusive gateway {gw_id} has fewer than 2 outgoing flows")
        default_id = attr(gw, "default")
        if not default_id:
            fail(f"exclusive gateway {gw_id} has no default flow")
        for flow in outgoing:
            fid = attr(flow, "id")
            has_condition = (
                flow.find(
                    "bpmn:conditionExpression",
                    {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"},
                )
                is not None
            )
            if fid != default_id and not has_condition:
                fail(f"non-default flow {fid} from gateway {gw_id} has no condition")

    print(f"OK: {path} is well-formed, fully shaped, and gateway-routed")


if __name__ == "__main__":
    main()
