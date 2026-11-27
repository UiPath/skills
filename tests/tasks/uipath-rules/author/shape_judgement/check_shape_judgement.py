#!/usr/bin/env python3
"""Grades the shape the agent chose for a policy whose prompt names no shape.

`single`: ShippingRules answers one value, so it stays one decision, though the policy
walks through an "oversized" step first. `shared`: ClaimsRules decides a claim tier once
and two answers read it, so the tier is its own decision required by both, not a
knowledge model. `model`: MemberPrices runs one price calculation on two different
arguments, so the calculation is a knowledge model each answer calls. A call is FEEL the
offline evaluator does not run, so `model` grades structure only.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    check_graph_cases,
    check_knowledge_models,
    decision_for_output,
    executable_text,
    knowledge_models,
    model_calls,
    required,
)
from rules_check import check_cases, fail, find_project, load_graph, load_rule, table_of  # noqa: E402

SHIPPING = [({"weightKg": weight, "zone": zone}, "Freight" if weight > 30 else {"Domestic": "Post", "International": "Courier"}[zone])
            for weight in (0, 12.5, 30, 30.01, 80) for zone in ("Domestic", "International")]
CLAIMS = [({"claimAmount": amount, "customerYears": years},
           {"approved": amount <= 10000 or years >= 5, "queue": "Senior" if amount > 10000 else "General"})
          for amount in (0, 10000, 10001, 250000) for years in (0, 4, 5, 20)]


def no_models(root) -> None:
    if knowledge_models(root):
        fail(f"the rule declares knowledge models {[m.get('name') for m in knowledge_models(root)]}; "
             f"nothing in this policy is a calculation run on different arguments")


def grade_single() -> None:
    _, root = load_rule(find_project("ShippingRules"))
    no_models(root)
    check_cases(table_of(root), "carrier", SHIPPING)
    print(f"OK: one decision, and all {len(SHIPPING)} cases return the carrier")


def grade_shared() -> None:
    _, root = load_graph(find_project("ClaimsRules"))
    no_models(root)
    approval, routing = decision_for_output(root, "approved"), decision_for_output(root, "queue")
    if approval is routing:
        fail("one decision answers both approved and queue; the business decides them separately")
    shared = set(required(approval, "requiredDecision")) & set(required(routing, "requiredDecision"))
    if not shared:
        fail("approved and queue require no common decision; the claim tier is decided once and read by both")
    check_graph_cases(root, CLAIMS)
    print(f"OK: the tier is one decision both answers require, and all {len(CLAIMS)} cases match")


def grade_model() -> None:
    _, root = load_graph(find_project("MemberPrices"))
    check_knowledge_models(root)
    models = [m.get("name") or "" for m in knowledge_models(root)]
    if not models:
        fail("no knowledge model holds the member price calculation, which runs on two different arguments")
    arguments = []
    for output in ("memberItemPrice", "memberDeliveryFee"):
        decision = decision_for_output(root, output)
        if "0.9" in executable_text(decision):
            fail(f"the decision answering {output} computes the discount itself instead of calling the model")
        calls = [call.strip() for model in models for call in model_calls(decision, model)]
        if not calls:
            fail(f"the decision answering {output} calls none of {models}")
        arguments.append(calls)
    if decision_for_output(root, "memberItemPrice") is decision_for_output(root, "memberDeliveryFee"):
        fail("one decision answers both prices; the caller reads them as two values")
    if arguments[0] == arguments[1]:
        fail(f"both prices call the model with {arguments[0]}; each passes its own price")
    print(f"OK: {models} holds the calculation, and each price calls it with its own argument")


if __name__ == "__main__":
    modes = {"single": grade_single, "shared": grade_shared, "model": grade_model}
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode not in modes:
        fail(f"mode must be one of {sorted(modes)}, got {mode!r}")
    modes[mode]()
