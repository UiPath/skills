#!/usr/bin/env python3
"""Structural check for the error-mapping expression eval.

Grades that the authored BPMN carries a uipath:errorMapping block whose
condition branches on the runtime error object via `vars.error.code` (matched
as an expression, not a baked literal), per references/expression-authoring.md.
Reuses the shared uipath-maestro-bpmn check helpers (stdlib ElementTree).
"""

from __future__ import annotations

import os
import re
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_check import (  # noqa: E402
    NS,
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

VARS_ERROR_RE = re.compile(r"vars\.error\.code")


def main() -> None:
    path, root = parse_bpmn("ErrorMappingBpmn")

    mappings = root.findall(".//uipath:errorMapping", NS)
    if not mappings:
        fail("no uipath:errorMapping block authored")

    conditions: list[str] = []
    for mapping in mappings:
        for err in mapping.findall("uipath:error", NS):
            cond = err.attrib.get("condition")
            if cond:
                conditions.append(cond)
    if not conditions:
        fail("uipath:errorMapping has no uipath:error carrying a condition")

    matching = [c for c in conditions if VARS_ERROR_RE.search(c)]
    if not matching:
        fail(f"no errorMapping condition reads vars.error.code; found: {conditions}")

    # Must be a runtime expression (leading '='), not a baked literal.
    if not any(c.strip().startswith("=") for c in matching):
        fail(f"vars.error.code condition must be an expression (leading '='): {matching}")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} branches on vars.error.code via uipath:errorMapping")


if __name__ == "__main__":
    main()
