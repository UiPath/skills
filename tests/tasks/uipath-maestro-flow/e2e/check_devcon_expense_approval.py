#!/usr/bin/env python3
"""Validate the DevCon expense approval flow's HITL semantics.

The task is intentionally about the workflow behavior, not the exact editing
mechanism. Inline HITL can be authored directly in the .flow file, and approval
can be represented either as a boolean output field or as approve/reject
outcomes.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path


FLOW_GLOB = "ExpenseApproval/ExpenseApproval/ExpenseApproval.flow"


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def load_flow() -> dict:
    matches = glob.glob(FLOW_GLOB)
    if not matches:
        fail(f"No flow file matching {FLOW_GLOB}")
    path = Path(matches[0])
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def field_text(field: dict, key: str) -> str:
    value = field.get(key)
    return value.lower() if isinstance(value, str) else ""


def main() -> None:
    flow = load_flow()
    nodes = flow.get("nodes")
    edges = flow.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        fail("Flow must contain nodes[] and edges[]")

    hitl_nodes = [n for n in nodes if n.get("type") == "uipath.human-in-the-loop"]
    if len(hitl_nodes) != 1:
        fail(f"Expected exactly one uipath.human-in-the-loop node, found {len(hitl_nodes)}")
    hitl = hitl_nodes[0]
    hitl_id = hitl.get("id")
    if not hitl_id:
        fail("HITL node is missing id")

    version = str(hitl.get("typeVersion", ""))
    if not version.startswith("1.0"):
        fail(f"HITL node typeVersion should be a v1.0 schema, found {version!r}")

    schema = hitl.get("inputs", {}).get("schema", {})
    fields = schema.get("fields")
    outcomes = schema.get("outcomes")
    if not isinstance(fields, list) or not fields:
        fail("HITL schema must define fields")
    if not isinstance(outcomes, list) or len(outcomes) < 2:
        fail("HITL schema must define at least two outcomes")

    if not any(
        (field_text(f, "id") == "amount" or "amount" in field_text(f, "label")) and f.get("type") == "number"
        for f in fields
    ):
        fail("Amount field must use type number")

    decision_fields = [
        f
        for f in fields
        if f.get("direction") in {"output", "inOut"}
        and ("approval" in field_text(f, "id") or "approved" in field_text(f, "id") or "decision" in field_text(f, "id"))
    ]
    has_boolean_decision = any(f.get("type") == "boolean" for f in decision_fields)
    outcome_names = {str(o.get("name") or o.get("id") or "").lower() for o in outcomes}
    has_approval_outcomes = any("approve" in name for name in outcome_names) and any(
        "reject" in name for name in outcome_names
    )
    if not (has_boolean_decision or has_approval_outcomes):
        fail("HITL must capture the manager decision as a boolean output or approve/reject outcomes")

    input_bindings = [
        f.get("binding", "")
        for f in fields
        if f.get("direction") in {"input", "inOut"} and isinstance(f.get("binding"), str)
    ]
    if not input_bindings:
        fail("HITL input fields must be bound to upstream script output")
    if not any(binding.startswith("=js:$vars.") and ".output." in binding for binding in input_bindings):
        fail("HITL input bindings must use =js:$vars.<node>.output.<field>")

    if not any(e.get("sourceNodeId") == hitl_id and e.get("sourcePort") == "completed" for e in edges):
        fail("HITL completed handle must be wired")

    scripts = [
        str(n.get("inputs", {}).get("script", ""))
        for n in nodes
        if n.get("type") == "core.action.script"
    ]
    expected_output_path = f"$vars.{hitl_id}.output"
    if not any(expected_output_path in script for script in scripts):
        fail(f"Downstream script must read HITL output via {expected_output_path}")

    print(f"OK: HITL node {hitl_id} uses v1.0 schema, captures approval, wires completed, and uses .output paths")


if __name__ == "__main__":
    main()
