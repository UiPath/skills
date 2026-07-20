#!/usr/bin/env python3
"""Structural check for the computed `=js:` expression eval.

Grades that the authored BPMN uses a computed inline-JavaScript expression with
the exact case-sensitive `=js:` prefix (no space after the colon) in a
lint-sensitive field, and that every json-typed literal body parses as valid
JSON, per references/expression-authoring.md. Reuses shared helpers (stdlib ET).
"""

from __future__ import annotations

import json
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


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def collect_values(root) -> list[str]:
    vals: list[str] = []
    for el in root.iter():
        for name in ("value", "source", "condition"):
            v = el.attrib.get(name)
            if v:
                vals.append(v)
        if el.text and el.text.strip():
            vals.append(el.text.strip())
    return vals


def main() -> None:
    path, root = parse_bpmn("ComputedJsBpmn")

    values = collect_values(root)

    # Exact, case-sensitive prefix with no space after the colon.
    if not any("=js:" in v for v in values):
        fail("no computed expression with the exact '=js:' prefix found")

    # Reject the common malformed variants so the case-sensitivity rule is graded.
    bad = [v for v in values if re.search(r"=(js\s*:|JS:|Js:|jS:)", v) and "=js:" not in v]
    if bad:
        fail(f"malformed js prefix (must be exactly '=js:', no space, lowercase): {bad}")

    # Every json-typed field carrying a literal body must be valid JSON.
    for el in root.iter():
        if local(el.tag) in ("input", "output") and el.attrib.get("type") == "json":
            body = (el.text or "").strip() or (el.attrib.get("value") or "").strip()
            if body.startswith("{") or body.startswith("["):
                try:
                    json.loads(body)
                except json.JSONDecodeError as exc:
                    fail(f"json-typed value is not valid JSON: {body[:80]!r} ({exc})")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)
    print(f"OK: {path} uses a computed =js: expression with valid json-typed bodies")


if __name__ == "__main__":
    main()
