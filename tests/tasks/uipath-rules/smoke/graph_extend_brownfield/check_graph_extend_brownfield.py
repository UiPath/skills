#!/usr/bin/env python3
"""Grades a freight decision added to PricingRules, a rule that already holds all three constructs.

The point is what survives. Every other brownfield fixture is decision tables
only, so nothing tested an agent editing a rule that already carries a
knowledge model, a literal-expression decision and a text annotation — the
things an agent that rewrites a file wholesale silently drops, as one did with
the diagram.

`kept` checks the rule still holds what it held. `wired` checks the new
decision calls the model that was already there instead of declaring a second
one. `diagram` checks the placed shapes stayed and the new element got one.
The freight figure itself is not graded: a call is FEEL the offline evaluator
does not run, and no engine task covers PricingRules.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    check_annotations_attached,
    check_entry_points_kept,
    check_graph_cases,
    check_knowledge_models,
    check_no_overlap,
    check_shapes_kept,
    decisions,
    knowledge_models,
    required,
)
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "PricingRules"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / PROJECT
TIER_CASES = [({"customerTier": tier}, {"tierPct": pct})
              for tier, pct in (("Gold", 15.0), ("Silver", 10.0), ("Standard", 0.0), ("Bronze", 0.0))]


def kept() -> None:
    """Everything the rule already held is still there, and still itself."""
    _, root = load_graph(find_project(PROJECT))

    models = {m.get("name") for m in knowledge_models(root)}
    if "discounted" not in models:
        fail(f"the knowledge model 'discounted' is gone; the rule now holds {sorted(models) or 'none'}")
    if len(models) > 1:
        fail(f"a second knowledge model appeared ({sorted(models)}); the freight discount reuses 'discounted'")

    literal = {d.get("name") for d in root.findall("dmn:decision", NS) if d.find("dmn:literalExpression", NS) is not None}
    if "netUnitPrice" not in literal:
        fail("the netUnitPrice decision is gone or is no longer a literal expression")

    notes = [n for n in root.findall("dmn:textAnnotation", NS) if "whole numbers" in (n.findtext("dmn:text", default="", namespaces=NS) or "")]
    if not notes:
        fail("the text annotation about whole-number percentages is gone")

    check_knowledge_models(root)
    check_annotations_attached(root)

    # Only the tier decision's values are graded. The freight decision is free to be a table whose
    # output cell calls the model — `discounted(50, tier)` — and `literal()` rightly refuses to read
    # a call as a value. Evaluating the whole graph here would kill a correct edit on that refusal,
    # and this task never runs the engine, so there is nothing to fall back to.
    check_graph_cases(_tier_only(root), TIER_CASES)
    print("OK: the model, the literal expression, the note and the tier values all survived the edit")


def _tier_only(root: ET.Element) -> ET.Element:
    """The rule with every decision but `tier` dropped, so the case set grades only what it names."""
    trimmed = ET.fromstring(ET.tostring(root))
    for decision in decisions(trimmed):
        if decision.get("name") != "tier":
            trimmed.remove(decision)
    return trimmed


def wired() -> None:
    """The freight decision calls the model that was already there."""
    _, root = load_graph(find_project(PROJECT))

    callers = [d for d in root.findall("dmn:decision", NS)
               if "bkm_discounted" in required(d, "requiredKnowledge")]
    names = {d.get("name") for d in callers}
    if "netUnitPrice" not in names:
        fail("netUnitPrice no longer requires 'discounted'")
    if len(callers) < 2:
        fail(f"only {sorted(names)} requires 'discounted'; the freight decision should call it too")

    freight = [d for d in callers if d.get("name") != "netUnitPrice"]
    for decision in freight:
        if not any("discounted(" in text for text in decision.itertext() if text):
            fail(f"decision {decision.get('name')!r} requires 'discounted' but its logic never calls it")
    print(f"OK: {len(callers)} decisions call 'discounted', each with its own arguments")


def diagram() -> None:
    """The shapes the fixture placed are where they were, and the new element has one."""
    project = find_project(PROJECT)
    _, root = load_graph(project)
    check_shapes_kept(ET.parse(FIXTURE / "Business rule.dmn").getroot(), root)
    check_no_overlap(root)
    check_entry_points_kept(project, FIXTURE)
    print("OK: the placed shapes are where they were, every element is placed, and the entry points are kept")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    {"kept": kept, "wired": wired, "diagram": diagram}.get(mode, lambda: fail("mode: kept | wired | diagram"))()
