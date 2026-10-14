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
from _shared.graph import reachable  # noqa: E402


def _output_var_ids(script) -> set[str]:
    ids = set()
    for out in script.findall(".//uipath:output", NS):
        var = out.attrib.get("var")
        if var:
            ids.add(var)
    return ids


def _read_text(script) -> str:
    # The args input is a fixed {vars, metadata} envelope; reads live in the
    # script body as vars.<id>.
    parts = []
    for inp in script.findall(".//uipath:input", NS):
        parts.append(text_content(inp))
        parts.append(" ".join(inp.attrib.values()))
    body = script.find("bpmn:script", NS)
    if body is not None:
        parts.append(text_content(body))
    return " ".join(parts)


def _require_variable_passing(root, scripts) -> None:
    """Every script task but the head reads a variable an ancestor produced.

    Ancestry comes from the sequence flows. Matching any two script tasks
    instead let a task satisfy the rule by naming a *downstream* task's output,
    and let every task after the second skip variable passing entirely, while
    the prompt requires it of each one.
    """
    reads = {attr(s, "id"): _read_text(s) for s in scripts}
    produces = {attr(s, "id"): _output_var_ids(s) for s in scripts}
    downstream = {sid: reachable(root, sid) for sid in reads}

    heads, starved = [], []
    for sid in reads:
        ancestors = [other for other in reads if other != sid and sid in downstream[other]]
        if not ancestors:
            heads.append(sid)
            continue
        if not any(vid and vid in reads[sid] for a in ancestors for vid in produces[a]):
            starved.append(sid)

    if starved:
        fail(
            "script task(s) "
            + ", ".join(sorted(starved))
            + " read no variable produced by a script task upstream of them; the"
            " pipeline must pass its value through each step"
        )
    # Without this the rule above is vacuous on a file whose script tasks are
    # not wired to each other: no task has an ancestor, so none can starve.
    if len(heads) != 1:
        fail(
            f"expected one linear script-task chain with a single head, found {len(heads)} "
            f"script task(s) with no upstream script task: {', '.join(sorted(heads)) or 'none'}"
        )


def main() -> None:
    path, root = parse_bpmn("FeetInchesBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")

    scripts = elements(root, "scriptTask")
    if len(scripts) < 3:
        fail(f"expected a pipeline of at least 3 script tasks, found {len(scripts)}")

    _require_variable_passing(root, scripts)

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} is a sequential script-task pipeline with variable passing between nodes")


if __name__ == "__main__":
    main()
