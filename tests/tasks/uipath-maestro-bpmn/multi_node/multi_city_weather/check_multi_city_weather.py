#!/usr/bin/env python3
"""Structural check for the multi_city_weather BPMN port.

Enforces the ported intent: a PARALLEL multi-instance marker over a per-item
script task, with the cities collection bound through uipath:loopCharacteristics.
Grades authored XML shape.
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
    path, root = parse_bpmn("MultiCityWeatherBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")
    one_or_more(root, "scriptTask")

    markers = root.findall(".//bpmn:multiInstanceLoopCharacteristics", NS)
    if not markers:
        fail("no bpmn:multiInstanceLoopCharacteristics marker authored")

    parallel = [m for m in markers if m.attrib.get("isSequential") == "false"]
    if not parallel:
        fail("multi-instance marker must be parallel (isSequential=\"false\") for per-city fan-out")

    bound = False
    for m in parallel:
        lc = m.find(".//uipath:loopCharacteristics", NS)
        if lc is not None and lc.attrib.get("inputCollection") and lc.attrib.get("inputElement"):
            bound = True
    if not bound:
        fail("parallel multi-instance marker missing uipath:loopCharacteristics inputCollection/inputElement binding")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} classifies cities through a parallel multi-instance script task")


if __name__ == "__main__":
    main()
