#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import (  # noqa: E402
    NS,
    attr,
    elements,
    fail,
    has_uipath_extension,
    parse_bpmn,
    require_di_for_visible_elements,
    require_sequence_integrity,
    text_content,
)

FORBIDDEN = [
    "require(",
    "import ",
    "fetch(",
    "XMLHttpRequest",
    "process.",
    "fs.",
    "setTimeout",
    "setInterval",
    "window.",
    "document.",
    "await ",
]


def main() -> None:
    path, root = parse_bpmn("RiskScoreScriptBpmn")
    scripts = elements(root, "scriptTask")
    if not scripts:
        fail("missing bpmn:scriptTask")
    task = scripts[0]
    if attr(task, "scriptFormat").lower() != "javascript":
        fail('script task must set scriptFormat="JavaScript"')
    if not has_uipath_extension(task, "scriptVersion"):
        fail("script task missing uipath:scriptVersion metadata")
    script = task.find("bpmn:script", NS)
    if script is None or not text_content(script).strip():
        fail("script task is missing bpmn:script content")
    body = text_content(script)
    present = [token for token in FORBIDDEN if token in body]
    if present:
        fail(f"script uses APIs outside the Jint boundary: {present}")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains a Jint-compatible BPMN script task")


if __name__ == "__main__":
    main()
