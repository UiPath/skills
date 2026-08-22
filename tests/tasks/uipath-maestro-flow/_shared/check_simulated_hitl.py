#!/usr/bin/env python3
"""Check source semantics for the simulated HITL tasks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from flow_check import find_flow_file


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load_flow() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = Path(find_flow_file())
    try:
        flow = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"could not read {path}: {error}")
    nodes = flow.get("nodes")
    if not isinstance(nodes, list):
        fail(f"{path} has no nodes array")
    return flow, nodes


def hitl_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        node
        for node in nodes
        if str(node.get("type", "")).startswith("uipath.human-in-the-loop")
    ]


def check_quick_form(_flow: dict[str, Any], nodes: list[dict[str, Any]]) -> None:
    candidates = [
        node
        for node in hitl_nodes(nodes)
        if node.get("type") == "uipath.human-in-the-loop.quick-form"
        or (
            node.get("type") == "uipath.human-in-the-loop"
            and (node.get("inputs") or {}).get("type") == "quick"
        )
    ]
    if not candidates:
        fail(
            "need an inline HITL quick form: either the quick-form node type or "
            "the base HITL node with inputs.type='quick'"
        )
    print("OK: flow contains an inline HITL quick form")


def field_text(field: dict[str, Any], key: str) -> str:
    value = field.get(key)
    return value.lower() if isinstance(value, str) else ""


def check_schema(flow: dict[str, Any], nodes: list[dict[str, Any]]) -> None:
    candidates = hitl_nodes(nodes)
    if not candidates:
        fail("need a HITL quickform node")
    fields = (candidates[0].get("inputs") or {}).get("schema", {}).get("fields", [])
    directions = {field.get("direction") for field in fields}
    if "input" not in directions:
        fail("need an input-direction (read-only) field")
    if not directions.intersection({"output", "inOut"}):
        fail("need an output/inOut (fill-in) field")
    rendered = json.dumps(flow).lower()
    if "approve" not in rendered or "reject" not in rendered:
        fail("need Approve and Reject outcomes")
    print("OK: HITL schema has input/output fields and Approve/Reject outcomes")


def check_priority(_flow: dict[str, Any], nodes: list[dict[str, Any]]) -> None:
    candidates = hitl_nodes(nodes)
    if not candidates:
        fail("need a HITL quickform node")
    if "high" not in json.dumps(candidates[0]).lower():
        fail("priority should be High")
    print("OK: HITL priority is High")


def check_expense(flow: dict[str, Any], nodes: list[dict[str, Any]]) -> None:
    edges = flow.get("edges")
    if not isinstance(edges, list):
        fail("Flow must contain edges[]")
    candidates = hitl_nodes(nodes)
    if len(candidates) != 1:
        fail(f"need exactly 1 HITL node, found {len(candidates)}")
    hitl = candidates[0]
    hitl_id = hitl.get("id")
    schema = (hitl.get("inputs") or {}).get("schema", {})
    fields = schema.get("fields", [])
    outcomes = schema.get("outcomes", []) or []
    if not fields:
        fail("HITL needs fields")
    if not any(
        (field_text(field, "id") == "amount" or "amount" in field_text(field, "label"))
        and field.get("type") == "number"
        for field in fields
    ):
        fail("amount must be a number field")
    decision_fields = [
        field
        for field in fields
        if field.get("direction") in {"output", "inOut"}
        and any(
            key in field_text(field, "id")
            for key in ("approval", "approved", "decision")
        )
    ]
    outcome_names = {
        str(outcome.get("name") or outcome.get("id") or "").lower()
        for outcome in outcomes
    }
    has_decision = any(field.get("type") == "boolean" for field in decision_fields)
    has_outcomes = any("approve" in name for name in outcome_names) and any(
        "reject" in name for name in outcome_names
    )
    if not (has_decision or has_outcomes):
        fail("need a boolean decision field or approve/reject outcomes")
    reason_keys = ("reason", "comment", "explanation", "justification", "note")
    if not any(
        field.get("direction") in {"output", "inOut"}
        and field.get("type") in {"text", "string", "textarea"}
        and any(
            key in field_text(field, "id") or key in field_text(field, "label")
            for key in reason_keys
        )
        for field in fields
    ):
        fail("need a text reason output field")
    if not any(
        edge.get("sourceNodeId") == hitl_id
        and edge.get("sourcePort") in {"completed", "outcome-completed"}
        for edge in edges
    ):
        fail("HITL completed handle must be wired")
    scripts = [
        str((node.get("inputs") or {}).get("script", ""))
        for node in nodes
        if node.get("type") == "core.action.script"
    ]
    expected = f"$vars.{hitl_id}.output"
    if not any(expected in script for script in scripts):
        fail(f"downstream script must read HITL output via {expected}")
    print("OK: expense HITL schema, routing, and downstream output access are correct")


CHECKS = {
    "expense": check_expense,
    "priority": check_priority,
    "quick-form": check_quick_form,
    "schema": check_schema,
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=sorted(CHECKS))
    args = parser.parse_args()
    flow, nodes = load_flow()
    CHECKS[args.check](flow, nodes)


if __name__ == "__main__":
    main()
