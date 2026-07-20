#!/usr/bin/env python3
"""Structural check for the reading_list BPMN port.

Enforces the ported intent: two distinct sequential script tasks - one that
filters the catalog (difficulty/pages predicate) and one that maps survivors to
an uppercased title + author. Grades authored XML shape.
"""

from __future__ import annotations

import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)

from _shared.bpmn_check import (  # noqa: E402
    elements,
    fail,
    one_or_more,
    parse_bpmn,
    require_di_for_visible_elements,
    require_no_private_connector_values,
    require_sequence_integrity,
    text_content,
)


def main() -> None:
    path, root = parse_bpmn("ReadingListBpmn")

    one_or_more(root, "startEvent")
    one_or_more(root, "endEvent")

    scripts = elements(root, "scriptTask")
    if len(scripts) < 2:
        fail(f"expected at least 2 script tasks (filter + map), found {len(scripts)}")

    bodies = [text_content(s).lower() for s in scripts]
    has_filter = any(
        ("difficulty" in b or "pages" in b or "filter" in b) for b in bodies
    )
    has_map = any(("touppercase" in b or "map" in b or "toupper" in b) for b in bodies)
    if not has_filter:
        fail("no script task applies the filter predicate (difficulty/pages)")
    if not has_map:
        fail("no script task maps survivors (expected an uppercase title transform)")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} curates the catalog through distinct filter and map script tasks")


if __name__ == "__main__":
    main()
