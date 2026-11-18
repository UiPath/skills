#!/usr/bin/env python3
"""Grades UnderwritingRules, authored from `policy.md`: eight outputs, several of them derived from others.

A reference implementation of the policy gives the expected value of every
output for each case. `structure` checks the dependent outputs come from
decisions that require the ones they build on.
"""

from __future__ import annotations

import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "_shared"))

from graph_check import check_chain, check_graph_cases, check_no_overlap  # noqa: E402
from rules_check import fail, find_project, load_graph  # noqa: E402

PROJECT = "UnderwritingRules"
CHAINS = [
    ("baseRate", "riskBand"), ("baseRate", "loanSize"),
    ("loyaltyDiscount", "stability"),
    ("eligibility", "riskBand"), ("eligibility", "affordability"),
    ("approvalRoute", "eligibility"), ("approvalRoute", "loanSize"), ("approvalRoute", "stability"),
]


def expected(case: dict) -> dict:
    score, income = case["creditScore"], case["income"]
    band = "High" if score < 580 else "Low" if score >= 700 else "Medium" if income >= 50000 else "High"
    ratio = case["debtRatio"]
    affordability = "Good" if ratio <= 0.3 else "Fair" if ratio <= 0.45 else "Poor"
    stability = "Stable" if case["employmentYears"] >= 2 else "New"
    amount = case["loanAmount"]
    size = "Small" if amount < 25000 else "Standard" if amount < 100000 else "Large"
    large = size == "Large"
    rate = 12.5 if band == "High" else (9 if large else 8) if band == "Medium" else (6 if large else 5.5)
    discount = 0 if not case["existingCustomer"] else 0.5 if stability == "Stable" else 0.25
    if band == "High" or affordability == "Poor":
        eligibility = "Declined"
    elif band == "Medium" and affordability == "Fair":
        eligibility = "Review"
    else:
        eligibility = "Eligible"
    if eligibility == "Declined":
        route = "Reject"
    elif eligibility == "Review" or large or stability == "New":
        route = "Manual"
    else:
        route = "Auto"
    return {"riskBand": band, "affordability": affordability, "stability": stability, "loanSize": size,
            "baseRate": rate, "loyaltyDiscount": discount, "eligibility": eligibility, "approvalRoute": route}


GRID = {
    "creditScore": (550, 650, 720),
    "income": (40000, 60000),
    "loanAmount": (20000, 50000, 150000),
    "debtRatio": (0.3, 0.4, 0.5),
    "employmentYears": (1, 2),
    "existingCustomer": (True, False),
}
CASES = [(case, expected(case)) for case in (dict(zip(GRID, values)) for values in itertools.product(*GRID.values()))]


def check_structure() -> None:
    _, root = load_graph(find_project(PROJECT))
    for downstream, upstream in CHAINS:
        check_chain(root, downstream, upstream)
    check_no_overlap(root)
    print(f"OK: all {len(CHAINS)} dependencies are requirements between decisions, and no cards overlap")


def check_behavior() -> None:
    _, root = load_graph(find_project(PROJECT))
    check_graph_cases(root, CASES)
    print(f"OK: all {len(CASES)} cases return the expected value for every output")


if __name__ == "__main__":
    {"structure": check_structure, "behavior": check_behavior}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: fail("mode: structure | behavior"))()
