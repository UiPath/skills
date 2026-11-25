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
    answering_cell,
    check_annotations_attached,
    check_entry_points_kept,
    check_graph_cases,
    check_knowledge_models,
    check_no_overlap,
    check_shapes_kept,
    decision_for_output,
    decisions,
    knowledge_models,
    model_calls,
    reference_name,
    required,
    sole_call_arguments,
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

    # Still a literal expression is not still the same literal expression: replacing its body
    # with `0` keeps the name, the kind of node, the wiring and the entry point, and the only
    # values graded below are the tier decision's. The fixture's own text is the contract.
    _same_text(root, "dmn:decision[@id='decision_netUnitPrice']/dmn:literalExpression/dmn:text",
               "the netUnitPrice formula")
    _same_text(root, "dmn:businessKnowledgeModel[@id='bkm_discounted']/dmn:encapsulatedLogic"
                     "/dmn:literalExpression/dmn:text", "the body of the 'discounted' model")
    _same_parameters(root)

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


def _same_text(root: ET.Element, path: str, what: str) -> None:
    """`path` holds the text the fixture left there, whitespace aside."""
    fixture = ET.parse(FIXTURE / "Business rule.dmn").getroot()
    before = (fixture.findtext(path, default="", namespaces=NS) or "").strip()
    after = (root.findtext(path, default="", namespaces=NS) or "").strip()
    if not before:
        fail(f"the fixture has no {what}; the grader is out of step with it")
    if after != before:
        fail(f"{what} changed from {before!r} to {after!r}; the edit was to add a decision, not rewrite one")


def _same_parameters(root: ET.Element) -> None:
    """The 'discounted' model still takes the parameters its callers pass, in order."""
    def names(tree: ET.Element) -> list[tuple[str | None, str | None]]:
        return [(p.get("name"), p.get("typeRef")) for p in tree.findall(
            "dmn:businessKnowledgeModel[@id='bkm_discounted']/dmn:encapsulatedLogic/dmn:formalParameter", NS)]
    before, after = names(ET.parse(FIXTURE / "Business rule.dmn").getroot()), names(root)
    if after != before:
        fail(f"the 'discounted' model now takes {after}, not {before}; its callers pass the old signature")


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

    # The prompt asks for freight of 50 discounted by the customer's tier. Any second caller used
    # to satisfy this, so `shipping` calling `discounted(500, tier)` graded as correct.
    freight = decision_for_output(root, "freight")
    if freight.get("name") == "netUnitPrice":
        fail("netUnitPrice answers under 'freight'; the freight discount belongs in its own decision")
    if not model_calls(freight, "discounted"):
        fail(f"decision {freight.get('name')!r} requires 'discounted' but its logic never calls it; "
             f"a mention in an annotation is not a call")
    _freight_values(root, freight)
    print(f"OK: {len(callers)} decisions call 'discounted', and the freight comes out right for every tier")


def _freight_values(root: ET.Element, freight: ET.Element) -> None:
    """What the freight decision answers for each tier, taken from the row that actually fires.

    Reading the first cell that held a call graded one tier and let every other row say anything
    — `discounted(50, tier)` for Gold and 0 for the rest passed. The answering row is resolved
    per tier instead, and `kept()` has already pinned the model's body to the fixture's
    `amount * (1 - pct / 100)`, so the cell's arguments are enough to say what it returns.
    """
    # The tier decision has one output, so its result is that value and a reader addresses the
    # decision itself. `tier.tierPct` reads a field of a number and is what Critical Rule 3
    # exists to prevent; allowing it would grade an invalid call as correct, and this task never
    # runs the engine to catch it.
    tier_name = reference_name(decision_for_output(root, "tierPct"))
    for inputs, answer in TIER_CASES:
        percentage = answer["tierPct"]
        cell = answering_cell(freight, {**inputs, tier_name: percentage})
        arguments = [argument.strip() for argument in sole_call_arguments(cell, "discounted").split(",")]
        if len(arguments) != 2:
            fail(f"for {inputs} the freight answers discounted({', '.join(arguments)}); 'discounted' "
                 f"takes an amount and a percentage")
        if arguments[1] != tier_name:
            fail(f"for {inputs} the freight discount is taken at {arguments[1]!r}, not at {tier_name!r}, "
                 f"the tier percentage the rule already computes; {tier_name!r} has one output, so a "
                 f"reader names the decision and never a field of it")
        try:
            base = float(arguments[0])
        except ValueError:
            fail(f"for {inputs} the freight discount is taken on {arguments[0]!r}; the prompt asks for "
                 f"a flat 50 before discount")
        returned, expected = base * (1 - percentage / 100), 50 * (1 - percentage / 100)
        if returned != expected:
            fail(f"for {inputs} the freight returns {returned}, expected {expected}; the prompt asks "
                 f"for a flat 50 discounted by the tier")


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
