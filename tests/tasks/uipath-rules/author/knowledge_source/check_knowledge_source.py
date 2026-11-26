#!/usr/bin/env python3
"""Grades SpendRules, whose approval follows a cited policy: a knowledge source on the diagram.

The policy is one `knowledgeSource` the approval decision cites with `authorityRequirement`
/ `requiredAuthority`. Nothing connects to it any other way: an `informationRequirement` or a
`knowledgeRequirement` to it is not a citation, and the designer offers neither. The approval
values are graded too, and the diagram must place the source with no card overlapping another.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_graph_cases, check_no_overlap, decision_for_output, required  # noqa: E402
from rules_check import NS, fail, find_project, load_graph  # noqa: E402

PROJECT = "SpendRules"
CASES = [({"onboarded": onboarded, "spend": spend}, {"approved": onboarded and spend <= 25000})
         for onboarded in (True, False) for spend in (0, 25000, 25001, 90000)]


def is_policy(source) -> bool:
    text = f"{source.get('label') or ''} {source.get('name') or ''}"
    return "procurementpolicy" in re.sub(r"[^a-z]", "", text.lower())


def main() -> None:
    _, root = load_graph(find_project(PROJECT))
    sources = root.findall("dmn:knowledgeSource", NS)
    policies = [s for s in sources if is_policy(s)]
    if len(policies) != 1:
        fail(f"expected one knowledge source for the Procurement Policy, found {len(policies)} "
             f"among {[s.get('label') or s.get('name') for s in sources]}")
    policy = policies[0].get("id")

    source_ids = {s.get("id") for s in sources}
    for element in root:
        for kind in ("requiredInput", "requiredDecision", "requiredKnowledge"):
            for reference in element.iter(f"{{{NS['dmn']}}}{kind}"):
                if (reference.get("href") or "").lstrip("#") in source_ids:
                    fail(f"{element.get('id')} points at a knowledge source with {kind}; a source is cited with requiredAuthority")
    for source in sources:
        for kind in ("requiredInput", "requiredDecision", "requiredKnowledge"):
            if source.findall(f"dmn:authorityRequirement/dmn:{kind}", NS):
                fail(f"knowledge source {source.get('id')} cites a decision, input or model; a source cites only another source")

    approval = decision_for_output(root, "approved")
    if policy not in required(approval, "requiredAuthority"):
        fail(f"the approval decision does not cite {policy} with an authorityRequirement")
    check_graph_cases(root, CASES)
    check_no_overlap(root)
    print(f"OK: the approval cites the Procurement Policy as its authority, and all {len(CASES)} cases match")


if __name__ == "__main__":
    main()
