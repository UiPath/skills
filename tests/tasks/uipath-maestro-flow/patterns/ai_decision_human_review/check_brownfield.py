#!/usr/bin/env python3
"""Grades ai-decision-human-review inserted into BillingDisputeResolution: a
confidence gate on the auto-resolve route, a person behind it, the existing
posting step reached by both routes, and a rejection that never posts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import DECISION, END, SWITCH, fail, load_graph  # noqa: E402

ANALYST = "disputeAnalyst"
ROUTER = "routeByAction"
AUTO_PORT = "case-auto"
APPLY = "logCreditAmount"
POSTING_PREFIX = "uipath.core.api-workflow."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()

    original = json.loads((args.original / f"{args.original.name}.flow").read_text(encoding="utf-8"))
    original_ids = {n["id"] for n in original["nodes"]}
    g = load_graph(str(args.project / f"{args.project.name}.flow"))
    added = set(g.nodes) - original_ids

    gates = [n for n in g.ids(DECISION, SWITCH) if n in added and "confidence" in g.text(n)]
    if not gates:
        fail("no new decision reads the analyst's confidence")
    gate = gates[0]

    people = [n for n in g.hitl() if n in added]
    if not people:
        fail("no new human task reviews the low-confidence recommendation")

    # The person sits on the low-confidence side of the gate, not the confident one.
    if not g.routes_low(gate, people, ANALYST):
        fail(f"{gate} sends more than its below-the-threshold side to the person")

    auto = g.edges_from(ROUTER, AUTO_PORT)
    if len(auto) != 1:
        fail(f"{ROUTER} has {len(auto)} {AUTO_PORT} edges, need exactly one")
    entry = auto[0]["targetNodeId"]
    if entry != gate and not (entry in added and g.reaches(entry, gate)):
        fail(f"the auto-resolve route goes to {entry}, not through the confidence gate {gate}")

    if not g.reaches(gate, APPLY, blocked=people):
        fail(f"a confident auto-resolve no longer reaches {APPLY} without a person")
    if not any(g.reaches(p, APPLY) for p in people):
        fail(f"an approved review does not post the way auto-resolve does ({APPLY})")

    postings = g.ids(POSTING_PREFIX)
    original_postings = [n for n in original["nodes"] if str(n["type"]).startswith(POSTING_PREFIX)]
    if len(postings) != len(original_postings):
        fail(f"{len(postings)} posting step(s), the original has {len(original_postings)}: the action was duplicated")

    rejected = {
        n for p in people for n in g.reachable(p, blocked=postings)
        if g.type_of(n) == END and not any(g.reaches(post, n) for post in postings)
    }
    if not rejected:
        fail("no review outcome ends the flow without posting: a rejection still posts the credit")

    print(f"PASS: {gate} gates auto-resolve, {people[0]} reviews, approval reaches {APPLY}, rejection ends at {sorted(rejected)}")


if __name__ == "__main__":
    main()
