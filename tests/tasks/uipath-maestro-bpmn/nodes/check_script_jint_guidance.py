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


def strip_js_comments(script: str) -> str:
    result = []
    index = 0
    in_string: str | None = None
    while index < len(script):
        char = script[index]
        next_char = script[index + 1] if index + 1 < len(script) else ""
        if in_string:
            result.append(char)
            if char == "\\":
                if index + 1 < len(script):
                    result.append(script[index + 1])
                    index += 2
                    continue
            elif char == in_string:
                in_string = None
            index += 1
            continue
        if char in {'"', "'", "`"}:
            in_string = char
            result.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(script) and script[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(script) and not (
                script[index] == "*" and script[index + 1] == "/"
            ):
                index += 1
            index += 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


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
    body = strip_js_comments(text_content(script))
    present = [token for token in FORBIDDEN if token in body]
    if present:
        fail(f"script uses APIs outside the Jint boundary: {present}")
    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    print(f"OK: {path} contains a Jint-compatible BPMN script task")


if __name__ == "__main__":
    main()
