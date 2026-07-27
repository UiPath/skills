#!/usr/bin/env python3
"""Structural check for the loop_multiply BPMN port.

Enforces the ported intent: a SEQUENTIAL multi-instance marker over a script
task, with the collection bound through uipath:loopCharacteristics. Grades
authored XML shape.
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
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)


def main() -> None:
    path, root = parse_bpmn("LoopMultiplyBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")
    one_or_more(root, "scriptTask")

    markers = root.findall(".//bpmn:multiInstanceLoopCharacteristics", NS)
    if not markers:
        fail("no bpmn:multiInstanceLoopCharacteristics marker authored")

    sequential = [m for m in markers if m.attrib.get("isSequential") == "true"]
    if not sequential:
        fail("multi-instance marker must be sequential (isSequential=\"true\") for ordered accumulation")

    bound = False
    for m in sequential:
        lc = m.find(".//uipath:loopCharacteristics", NS)
        if lc is not None and lc.attrib.get("inputCollection") and lc.attrib.get("inputElement"):
            bound = True
    if not bound:
        fail("sequential multi-instance marker missing uipath:loopCharacteristics inputCollection/inputElement binding")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} multiplies a collection through a sequential multi-instance marker")


if __name__ == "__main__":
    main()
