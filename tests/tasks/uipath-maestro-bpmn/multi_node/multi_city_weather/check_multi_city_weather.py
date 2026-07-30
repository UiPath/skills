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
    text_content,
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
        fail(
            "multi-instance marker must be parallel "
            '(isSequential="false") for per-city fan-out'
        )

    bound = False
    for script in root.findall(".//bpmn:scriptTask", NS):
        marker = script.find("bpmn:multiInstanceLoopCharacteristics", NS)
        if marker is None or marker.attrib.get("isSequential") != "false":
            continue
        lc = marker.find(".//uipath:loopCharacteristics", NS)
        if lc is None or not lc.attrib.get("inputCollection"):
            continue
        if lc.attrib.get("inputElement"):
            fail(
                "task-level parallel marker must omit inputElement so the "
                "runtime iterator object remains available"
            )
        inputs = " ".join(
            " ".join(inp.attrib.values()) + " " + (inp.text or "")
            for inp in script.findall(".//uipath:input", NS)
        )
        body = script.find("bpmn:script", NS)
        if "=iterator" not in inputs:
            fail("multi-instance ScriptTask args must pass the iterator object")
        if body is None or "iterator.item" not in text_content(body):
            fail("task-level multi-instance script must read the current item as iterator.item")
        bound = True
    if not bound:
        fail("parallel task marker missing uipath:loopCharacteristics inputCollection binding")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} classifies cities through a parallel multi-instance script task")


if __name__ == "__main__":
    main()
