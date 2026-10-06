#!/usr/bin/env python3
"""AP inbox triage — completion (classifier / router) agent check.

Final-state only. Validates:
  1. Autonomous agent; agent.json schemas in sync with entry-points.json.
  2. Inputs `from`, `subject`, `body` exist and are templated into the
     messages with matching contentTokens.
  3. Output contract: `category` enum (6 values), `priority` enum (4 values),
     `referenceNumbers` array, `summary` string, `needsHumanReview` boolean.
  4. No tool / context / escalation resources — a pure completion agent.
  5. Evaluation sets hold at least one test case per category, and every
     test case only uses declared input fields.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_autonomous,
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_project_id,
    assert_schema_sync,
    fail,
    load,
    resources,
)

AGENT_DIR = Path(os.getcwd()) / "APTriageSol" / "APInboxTriageAgent"
INPUTS = ["from", "subject", "body"]
CATEGORIES = [
    "invoice_submission",
    "payment_status_inquiry",
    "invoice_dispute",
    "vendor_master_update",
    "statement_reconciliation",
    "other",
]
PRIORITIES = ["low", "normal", "high", "urgent"]


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {
            "category": [],
            "priority": [],
            "referenceNumbers": ["references", "referenceNumbersList"],
            "summary": [],
            "needsHumanReview": ["humanReview", "requiresHumanReview"],
        },
    )
    assert_enum(f["category"], "category", CATEGORIES)
    assert_enum(f["priority"], "priority", PRIORITIES)
    if f["referenceNumbers"].get("type") != "array":
        fail(f"referenceNumbers must be an array, got {f['referenceNumbers']!r}")
    if f["needsHumanReview"].get("type") != "boolean":
        fail(f"needsHumanReview must be a boolean, got {f['needsHumanReview']!r}")
    print("OK: referenceNumbers is an array and needsHumanReview is a boolean")


def check_no_resources() -> None:
    found = [f"{p.parent.name} ({d.get('$resourceType')})" for p, d in resources(AGENT_DIR)]
    if found:
        fail(f"completion agent should not declare resources, found: {found}")
    print("OK: no tools, contexts or escalations — pure completion agent")


def check_evals(in_schema: dict) -> None:
    sets_dir = AGENT_DIR / "evals" / "eval-sets"
    cases = []
    for path in sorted(sets_dir.glob("*.json")) if sets_dir.is_dir() else []:
        cases.extend(load(path).get("evaluations") or [])
    if not cases:
        fail(f"no evaluation test cases under {sets_dir}")
    declared = set((in_schema.get("properties") or {}).keys())
    for case in cases:
        extra = set((case.get("inputs") or {}).keys()) - declared
        if extra:
            fail(f"test case {case.get('name')!r} uses undeclared input keys {sorted(extra)}")
    blobs = [
        json.dumps(c.get("expectedOutput") or {}) + " " + str(c.get("expectedAgentBehavior") or "")
        for c in cases
    ]
    # Word-boundary match so "other" does not hit "another" or "other_x".
    uncovered = [
        c for c in CATEGORIES if not any(re.search(rf"\b{re.escape(c)}\b", b) for b in blobs)
    ]
    if uncovered:
        fail(f"{len(cases)} test case(s) do not cover categories {uncovered}")
    print(f"OK: {len(cases)} evaluation test case(s) cover all {len(CATEGORIES)} categories")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_has_fields(in_schema, "inputSchema", {f: [] for f in INPUTS})
    assert_inputs_referenced(agent, INPUTS)
    check_outputs(out_schema)
    check_no_resources()
    check_evals(in_schema)


if __name__ == "__main__":
    main()
