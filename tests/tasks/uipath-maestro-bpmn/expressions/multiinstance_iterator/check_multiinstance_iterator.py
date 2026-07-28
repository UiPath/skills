#!/usr/bin/env python3
"""Structural check for the multi-instance iterator-depth expression eval.

Grades that a multi-instance SUBPROCESS body reads the current item and loop
index at subprocess depth — `iterator[0].item` and `iterator[0].loopCounter`
(NOT the task-level `iterator.item`), per references/expression-authoring.md.
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
    fail,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
)

ITEM_RE = re.compile(r"iterator\[0\]\.item")
LOOPCTR_RE = re.compile(r"iterator\[0\]\.loopCounter")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def find_local(root, local_name: str) -> list:
    """Find elements by local name, case-insensitively — the skill's
    structural-bpmn.md documents `bpmn:SubProcess` in PascalCase while the
    spec/fixtures use camelCase, so accept both."""
    target = local_name.lower()
    return [el for el in root.iter() if local(el.tag).lower() == target]


def collect_values(root) -> list[str]:
    vals: list[str] = []
    for el in root.iter():
        for name in ("value", "source", "condition", "inputCollection", "inputElement"):
            v = el.attrib.get(name)
            if v:
                vals.append(v)
        if el.text and el.text.strip():
            vals.append(el.text.strip())
    return vals


def main() -> None:
    path, root = parse_bpmn("MultiInstanceIteratorBpmn")

    markers = find_local(root, "multiInstanceLoopCharacteristics")
    if not markers:
        fail("no bpmn:multiInstanceLoopCharacteristics marker authored")

    # The marker must sit on a subProcess so subprocess-depth indexing applies.
    on_subprocess = any(
        any(local(child.tag).lower() == "multiinstanceloopcharacteristics" for child in sp)
        for sp in find_local(root, "subProcess")
    )
    if not on_subprocess:
        fail(
            "multi-instance marker must sit on a bpmn:subProcess "
            "(subprocess-depth iterator indexing uses iterator[0])"
        )

    values = collect_values(root)
    if not any(ITEM_RE.search(v) for v in values):
        fail("no mapping/value reads iterator[0].item (subprocess-depth item access)")
    if not any(LOOPCTR_RE.search(v) for v in values):
        fail("no mapping/value reads iterator[0].loopCounter")

    # Guard against task-level depth leaking into the subprocess body.
    bare_item = re.compile(r"(?<!\])iterator\.item")
    if any(bare_item.search(v) for v in values):
        fail("subprocess body must not use task-level iterator.item; use iterator[0].item")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} reads iterator[0].item / iterator[0].loopCounter at subprocess depth")


if __name__ == "__main__":
    main()
