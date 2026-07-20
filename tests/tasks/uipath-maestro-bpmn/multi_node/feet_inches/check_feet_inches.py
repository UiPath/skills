#!/usr/bin/env python3
"""Structural check for the feet_inches BPMN port.

Enforces the ported intent: a linear pipeline of >= 3 script tasks where a value
flows through intermediate variables (variable passing). Grades authored XML
shape.
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
    elements,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
    text_content,
)


def _output_var_ids(script) -> set[str]:
    ids = set()
    for out in script.findall(".//uipath:output", NS):
        var = out.attrib.get("var")
        if var:
            ids.add(var)
    return ids


def _input_text(script) -> str:
    parts = []
    for inp in script.findall(".//uipath:input", NS):
        parts.append(text_content(inp))
        parts.append(" ".join(inp.attrib.values()))
    return " ".join(parts)


def main() -> None:
    path, root = parse_bpmn("FeetInchesBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")

    scripts = elements(root, "scriptTask")
    if len(scripts) < 3:
        fail(f"expected a pipeline of at least 3 script tasks, found {len(scripts)}")

    # Variable passing: some script's input references a variable id that another
    # script declares as an output.
    outputs = [(_output_var_ids(s), _input_text(s)) for s in scripts]
    passed = False
    for i, (_, in_text) in enumerate(outputs):
        for j, (out_ids, _) in enumerate(outputs):
            if i == j:
                continue
            if any(vid and vid in in_text for vid in out_ids):
                passed = True
                break
        if passed:
            break
    if not passed:
        fail("no downstream script task reads a variable produced by an upstream script task")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} is a sequential script-task pipeline with variable passing between nodes")


if __name__ == "__main__":
    main()
