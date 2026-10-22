#!/usr/bin/env python3
"""Grade a draft-mode Flow skeleton (phase 2 of the phases design).

Usage (cwd = sandbox root):
    python3 $REFERENCE_DIR/check_draft_skeleton.py <FlowName> [--trigger manual|scheduled]

A skeleton passes when the discovered ``<FlowName>.flow``:
  - starts with the requested trigger type;
  - has at least three ``core.logic.mock`` boxes, each labelled
    ``<action> [<Type>]``, optionally ``→ <value it produces>``;
  - has a real decision or switch whose arms carry outcome labels, not the
    ``True`` / ``False`` defaults;
  - uses no real activity node (connector, agent, HTTP, script, ...): the
    skeleton is drawn before any node is chosen;
  - has a ``format``-built layout, so the canvas draws it;
  - validates with ``uip maestro flow validate``.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared import validate_flow  # noqa: E402
from _shared.flow_check import find_flow_files  # noqa: E402

ALLOWED = {
    "core.logic.mock",
    "core.logic.decision",
    "core.logic.switch",
    "core.logic.merge",
    "core.logic.loop",
    "core.control.end",
    "stickyNote",
}
BOX_LABEL = re.compile(r"\S.*\[[^\]]+\](\s*→\s*\S.*)?")


def fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    if not argv:
        return fail("usage: check_draft_skeleton.py <FlowName> [--trigger manual|scheduled]")
    name, trigger = argv[0], "manual"
    if "--trigger" in argv:
        trigger = argv[argv.index("--trigger") + 1]

    flows = [f for f in find_flow_files() if os.path.basename(f) == f"{name}.flow"]
    if len(flows) != 1:
        return fail(f"expected one {name}.flow, found {flows or 'none'}")
    path = flows[0]
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    nodes = doc.get("nodes") or []
    types = [n.get("type", "") for n in nodes]

    triggers = [t for t in types if t.startswith("core.trigger.")]
    if triggers != [f"core.trigger.{trigger}"]:
        return fail(f"expected one core.trigger.{trigger}, found {triggers}")

    real = sorted({t for t in types if t not in ALLOWED and not t.startswith("core.trigger.")})
    if real:
        return fail(f"skeleton has real activity nodes: {real}")

    boxes = [n for n in nodes if n.get("type") == "core.logic.mock"]
    if len(boxes) < 3:
        return fail(f"expected >= 3 core.logic.mock boxes, found {len(boxes)}")
    unlabelled = [n.get("id") for n in boxes
                  if not BOX_LABEL.fullmatch((n.get("display") or {}).get("label", ""))]
    if unlabelled:
        return fail(f"boxes without an '<action> [<Type>]' label: {unlabelled}")

    routed = False
    for n in nodes:
        inputs = n.get("inputs") or {}
        if n.get("type") == "core.logic.decision":
            labels = {inputs.get("trueLabel"), inputs.get("falseLabel")}
            routed |= bool(labels - {None, "", "True", "False"})
        elif n.get("type") == "core.logic.switch":
            routed |= any((c or {}).get("label") for c in inputs.get("cases") or [])
    if not routed:
        return fail("no decision or switch with outcome-labelled arms")

    if not (doc.get("layout") or {}).get("nodes"):
        return fail("no layout block: `uip maestro flow format` did not run on the emitted file")

    print(f"Skeleton shape OK: {len(boxes)} boxes in {path}", flush=True)
    return validate_flow.main([path])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
