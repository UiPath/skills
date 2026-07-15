#!/usr/bin/env python3
"""Structural check for the group-by-transform script-task port.

Asserts a Jint-safe JavaScript script task performs a group-by transform
(grouping rows by a field and producing an aggregation): scriptFormat=
"JavaScript", scriptVersion v3, a mapped input and output, no non-Jint runtime
APIs, a diagram shape, and a source that implements a grouping + aggregation.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
)

FORBIDDEN_JS = ("require(", "fetch(", "XMLHttpRequest", "window.", "document.", "process.", "fs.")


def assert_script_task(root, source_must_match, label):
    tasks = elements(root, "scriptTask")
    if len(tasks) != 1:
        fail(f"expected exactly one scriptTask, found {len(tasks)}")
    task = tasks[0]

    if task.attrib.get("scriptFormat") != "JavaScript":
        fail('scriptTask must set scriptFormat="JavaScript"')

    script = task.find("bpmn:script", NS)
    if script is None or not (script.text or "").strip():
        fail("scriptTask has no bpmn:script source")
    source = script.text or ""
    bad = [t for t in FORBIDDEN_JS if t in source]
    if bad:
        fail(f"script uses non-Jint runtime APIs: {bad}")

    version = task.find("bpmn:extensionElements/uipath:scriptVersion", NS)
    if version is None or version.attrib.get("value") != "v3":
        fail('scriptTask must declare uipath:scriptVersion value="v3"')

    inputs = task.findall("bpmn:extensionElements/uipath:mapping/uipath:input", NS)
    outputs = task.findall("bpmn:extensionElements/uipath:mapping/uipath:output", NS)
    if not inputs:
        fail("scriptTask maps no input into the script")
    if not outputs:
        fail("scriptTask maps no output out of the script")

    for pattern in source_must_match:
        if not re.search(pattern, source, re.IGNORECASE):
            fail(f"script source does not implement a {label} transform (missing /{pattern}/)")

    shaped = {s.attrib.get("bpmnElement") for s in root.findall(".//bpmndi:BPMNShape", NS)}
    if attr(task, "id") not in shaped:
        fail(f"scriptTask {attr(task, 'id')} has no BPMNShape")
    return task


def main() -> None:
    path, root = parse_bpmn("TransformGroupByDemo")
    # Grouping signal: reduce( / reduce.call( / "group" naming / keyed loop build,
    # plus an aggregation signal.
    assert_script_task(
        root,
        [r"reduce\s*[(.]|group|(for|while)[\s\S]*\[", r"count|sum|average|avg|aggregate|total|\.length|push\s*\(|\+\s*1|\+="],
        "group-by/aggregation",
    )
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} has a Jint-safe scriptTask performing a group-by transform")


if __name__ == "__main__":
    main()
