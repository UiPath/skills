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
    body = script.find("bpmn:script", NS)
    if body is not None:
        parts.append(text_content(body))
    return " ".join(parts)


def main() -> None:
    path, root = parse_bpmn("FeetInchesBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")

    scripts = elements(root, "scriptTask")
    if len(scripts) < 3:
        fail(f"expected a pipeline of at least 3 script tasks, found {len(scripts)}")

    # Current v3 ScriptTasks pass the complete vars object through args and read
    # specific ids in the script body. Follow sequence-flow reachability so a
    # self-reference or a read from a later/disconnected task cannot pass.
    script_by_id = {s.attrib.get("id", ""): s for s in scripts}
    predecessors = {script_id: set() for script_id in script_by_id}
    adjacency: dict[str, set[str]] = {}
    for seq in elements(root, "sequenceFlow"):
        source = seq.attrib.get("sourceRef", "")
        target = seq.attrib.get("targetRef", "")
        adjacency.setdefault(source, set()).add(target)

    for upstream_id in script_by_id:
        pending = list(adjacency.get(upstream_id, ()))
        seen: set[str] = set()
        while pending:
            candidate = pending.pop()
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate in script_by_id:
                predecessors[candidate].add(upstream_id)
            pending.extend(adjacency.get(candidate, ()))

    for script_id, script in script_by_id.items():
        upstream_ids = predecessors[script_id]
        if not upstream_ids:
            continue
        upstream_outputs = set().union(
            *(_output_var_ids(script_by_id[upstream_id]) for upstream_id in upstream_ids)
        )
        if not any(var_id in _input_text(script) for var_id in upstream_outputs):
            fail(
                f"downstream script task {script_id!r} does not read a variable "
                "produced by an upstream script task"
            )

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} is a sequential script-task pipeline with variable passing between nodes")


if __name__ == "__main__":
    main()
