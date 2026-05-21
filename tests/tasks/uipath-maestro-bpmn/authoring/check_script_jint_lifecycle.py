#!/usr/bin/env python3
"""Assert the generated BPMN covers the script/Jint full lifecycle path."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_assertions import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    assert_has_shape,
    assert_package_lifecycle,
    fail,
    load_bpmn,
    mapping_inputs,
    mapping_outputs,
    one_element,
    variable_ids,
)

PROJECT = Path("ScriptNormalizer/ScriptNormalizer")
BPMN_NAME = "ScriptNormalizer.bpmn"
FORBIDDEN_JS = (
    "require(",
    "fetch(",
    "XMLHttpRequest",
    "window.",
    "document.",
    "process.",
    "fs.",
)


def main() -> None:
    root = load_bpmn(str(PROJECT / BPMN_NAME))
    task = one_element(root, "scriptTask")

    if task.attrib.get("scriptFormat") != "JavaScript":
        fail('scriptTask must set scriptFormat="JavaScript"')

    script = task.find(f"{{{BPMN_NS}}}script")
    if script is None or not (script.text or "").strip():
        fail("scriptTask must include bpmn:script source")
    source = script.text or ""
    forbidden = [token for token in FORBIDDEN_JS if token in source]
    if forbidden:
        fail(f"script source uses non-Jint runtime APIs: {forbidden}")
    if "return" not in source and "response" not in source:
        fail("script source should return or produce an explicit response value")

    version = task.find(
        f"./{{{BPMN_NS}}}extensionElements/{{{UIPATH_NS}}}scriptVersion"
    )
    if version is None or version.attrib.get("value") != "v3":
        fail('scriptTask must include uipath:scriptVersion value="v3"')

    if len(mapping_inputs(task)) < 1:
        fail("scriptTask should map declared input data into the script")
    outputs = mapping_outputs(task)
    if len(outputs) < 1:
        fail("scriptTask should map a response/output variable")

    declared = variable_ids(root)
    output_targets = {
        out.attrib.get("var") or out.attrib.get("target") for out in outputs
    }
    missing = sorted(
        target for target in output_targets if target and target not in declared
    )
    if missing:
        fail(f"script outputs target undeclared variables: {missing}")

    assert_has_shape(root, task.attrib["id"])
    start = one_element(root, "startEvent")
    assert_package_lifecycle(PROJECT, BPMN_NAME, start.attrib["id"])
    print(
        "OK: scriptTask uses JavaScript/v3 Jint-safe source and package lifecycle files"
    )


if __name__ == "__main__":
    main()
