#!/usr/bin/env python3
"""Grades DiscountRules, whose tier lookup sits in a business knowledge model the decision calls.

The structural contract, and the discounts the model itself answers. A model's
encapsulated logic is a decision table like any other, so the same evaluator
runs it — against the parameters the prompt pins, which is what makes the values
gradable without a tenant. A model with the tiers swapped used to pass.

The *decision's* discount is still graded nowhere: a call is FEEL the offline
evaluator does not run, and no engine task covers DiscountRules —
`graph_check.py engine` is wired to LoanRules and graph_formula_and_model_debug
covers FeeRules.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import (  # noqa: E402
    check_annotations_attached,
    check_knowledge_models,
    check_model_cases,
    check_no_overlap,
    knowledge_models,
    model_calls,
    model_parameters,
)
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "DiscountRules"
# The signature the prompt pins, in order. Order is not decoration: a caller passes arguments
# positionally -- `tierDiscount(customerTier, orderTotal)` -- so a model declaring them the other
# way round binds the tier to the total at run time. `evaluate_model` binds by name, so it would
# answer every case correctly while the engine got it wrong, which is the failure this task exists
# to catch rather than to reproduce.
MODEL_PARAMETERS = ["customerTier", "orderTotal"]
# Either side of the 1000 threshold for each tier, by the parameter names the prompt pins.
DISCOUNTS = [
    ({"customerTier": "Gold", "orderTotal": 0}, 10),
    ({"customerTier": "Gold", "orderTotal": 999}, 10),
    ({"customerTier": "Gold", "orderTotal": 1000}, 15),
    ({"customerTier": "Silver", "orderTotal": 500}, 5),
    ({"customerTier": "Silver", "orderTotal": 1000}, 7.5),
    ({"customerTier": "Standard", "orderTotal": 999}, 0),
    ({"customerTier": "Standard", "orderTotal": 2500}, 2),
]


def main() -> None:
    _, root = load_graph(find_project(PROJECT))
    check_knowledge_models(root)

    # The decision has to call the model, not inline the lookup it was asked to extract.
    models = {m.get("name") for m in knowledge_models(root)}
    callers = [d for d in root.findall("dmn:decision", NS)
               if d.findall("dmn:knowledgeRequirement/dmn:requiredKnowledge", NS)]
    if not callers:
        fail(f"no decision calls {sorted(models)}; the lookup was asked for as a knowledge model")

    # Read from the FEEL each caller runs, not from all of its descendant text: a decision can
    # inline the lookup and name the model in a rule annotation, which a text search reads as a call.
    for name in models:
        if not any(model_calls(caller, name or "") for caller in callers):
            fail(f"no decision's logic calls {name}(...), so the model is wired but never used")

    # What the model answers, not merely that it is there and called. The prompt pins the two
    # parameters, so the model that takes them evaluates like any other table against them.
    #
    # Found by its signature rather than by being the only model in the file: the prompt asks
    # for the tier lookup as a model and does not forbid a helper beside it, so demanding
    # exactly one would fail work that is correct.
    assert set(MODEL_PARAMETERS) == set(DISCOUNTS[0][0]), "the cases and the signature disagree"
    lookups = [m for m in knowledge_models(root) if model_parameters(m) == MODEL_PARAMETERS]
    if len(lookups) != 1:
        declared = {m.get("name"): model_parameters(m) for m in knowledge_models(root)}
        fail(f"{len(lookups)} knowledge models take {MODEL_PARAMETERS} in that order, expected "
             f"exactly one; the rule declares {declared}. The prompt pins the parameters and "
             f"their order, because a caller passes them positionally: declared the other way "
             f"round, the engine binds the tier to the order total")
    check_model_cases(lookups[0], DISCOUNTS)

    check_annotations_attached(root)
    check_no_overlap(root)
    print(f"OK: {sorted(models)} declared, called, answering all {len(DISCOUNTS)} discount cases, "
          f"annotated, and the diagram is whole")


if __name__ == "__main__":
    main()
