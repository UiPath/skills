#!/usr/bin/env python3
"""Structural check for the wiki_pageviews BPMN e2e port.

Enforces the ported intent: a fetch script task, an exclusive gateway that
routes an invalid-article failure to an "Article not found" end, and two
distinct success-path script tasks (filter high-traffic days, then aggregate the
total), plus complete package metadata. Grades authored XML/JSON shape.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

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

PROJECT = Path.cwd() / "WikiPageviews"
BPMN_NAME = "WikiPageviews.bpmn"
REQUIRED_FILES = [
    "project.uiproj",
    "bindings_v2.json",
    "entry-points.json",
    "operate.json",
    "package-descriptor.json",
]


def load_json(name: str):
    p = PROJECT / name
    if not p.is_file():
        fail(f"{name} is missing")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        fail(f"{name} is not valid JSON: {exc}")


def main() -> None:
    for name in REQUIRED_FILES:
        if not (PROJECT / name).is_file():
            fail(f"{name} is missing")

    path, root = parse_bpmn("WikiPageviews")

    process = one_or_more(root, "process")[0]
    if process.attrib.get("isExecutable") != "true":
        fail("BPMN process must be executable")

    scripts = elements(root, "scriptTask")
    if len(scripts) < 3:
        fail(f"expected at least 3 script tasks (fetch + filter + aggregate), found {len(scripts)}")

    bodies = [text_content(s).lower() for s in scripts]
    if not any("500" in b or "views" in b for b in bodies):
        fail("no script task filters high-traffic days (expected a views > 500 predicate)")
    if not any(("reduce" in b or "sum" in b or "aggregate" in b or "+=" in b) for b in bodies):
        fail("no script task aggregates the surviving views into a total")

    gateways = one_or_more(root, "exclusiveGateway")
    flows = elements(root, "sequenceFlow")
    routed = False
    for gw in gateways:
        gw_id = attr(gw, "id")
        outgoing = [f for f in flows if attr(f, "sourceRef") == gw_id]
        if len(outgoing) < 2:
            continue
        default_id = attr(gw, "default")
        if not default_id:
            fail(f"exclusive gateway {gw_id} has no default flow")
        conditioned = [
            f for f in outgoing
            if attr(f, "id") != default_id and f.find("bpmn:conditionExpression", NS) is not None
        ]
        if not conditioned:
            fail(f"exclusive gateway {gw_id} has no conditioned (invalid-article) branch")
        routed = True
    if not routed:
        fail("no exclusive gateway routing the invalid-article failure")

    if "article not found" not in Path(path).read_text(encoding="utf-8").lower():
        fail('the invalid-article path must yield the literal "Article not found"')

    if len(elements(root, "endEvent")) < 2:
        fail("expected an end event for the error path and the success path")

    require_sequence_integrity(root)
    require_di_for_visible_elements(root)
    require_no_private_connector_values(root)

    for name in ("entry-points.json", "operate.json", "package-descriptor.json"):
        if BPMN_NAME not in json.dumps(load_json(name)):
            fail(f"{name} must reference {BPMN_NAME}")

    print(f"OK: {path} fetches, routes failure, filters, aggregates, and ships consistent package metadata")


if __name__ == "__main__":
    main()
