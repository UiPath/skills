#!/usr/bin/env python3
"""Structural check for the dice_roller BPMN port.

Enforces the ported intent: a script task that produces a random value and an
exclusive gateway that routes on the result. Grades authored XML shape.
"""

from __future__ import annotations

import os
import sys

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
    text_content,
)


def main() -> None:
    path, root = parse_bpmn("DiceRollerBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")

    scripts = one_or_more(root, "scriptTask")
    if not any("random" in text_content(s).lower() for s in scripts):
        fail("no script task uses randomness (expected Math.random or similar) to roll the die")

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
            fail(f"exclusive gateway {gw_id} has no conditioned branch on the roll result")
        routed = True

    if not routed:
        fail("no exclusive gateway classifying the roll into two branches")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} rolls a die in a script task and classifies it through an exclusive gateway")


if __name__ == "__main__":
    main()
