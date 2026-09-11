#!/usr/bin/env python3
"""Validate the DevCon expense approval flow's HITL semantics.

The task is intentionally about the workflow behavior, not the exact editing
mechanism. Inline HITL can be authored directly in the .flow file, and approval
can be represented either as a boolean output field or as approve/reject
outcomes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).resolve().parents[1] / "_shared"
sys.path.insert(0, str(SHARED_DIR))
try:
    from flow_check import find_flow_file  # noqa: E402
except ModuleNotFoundError as exc:
    if exc.name != "flow_check":
        raise
    from _shared.flow_check import find_flow_file  # noqa: E402

FLOW_GLOB = "ExpenseApproval*.flow"


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def load_flow() -> dict:
    path = Path(find_flow_file(flow_glob=FLOW_GLOB))
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def field_text(field: dict, key: str) -> str:
    value = field.get(key)
    return value.lower() if isinstance(value, str) else ""


def is_upstream_output_binding(binding: str) -> bool:
    return (
        binding.startswith("vars.") or binding.startswith("=js:$vars.")
    ) and ".output." in binding


def main() -> None:
    flow = load_flow()
    nodes = flow.get("nodes")
    edges = flow.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        fail("Flow must contain nodes[] and edges[]")

    hitl_nodes = [n for n in nodes if str(n.get("type", "")).startswith("uipath.human-in-the-loop")]
    if len(hitl_nodes) != 1:
        fail(f"Expected exactly one HITL node, found {len(hitl_nodes)}")
    hitl = hitl_nodes[0]
    hitl_id = hitl.get("id")
    if not hitl_id:
        fail("HITL node is missing id")

    version = str(hitl.get("typeVersion", ""))
    if not version.startswith("1."):
        fail(f"HITL node typeVersion should be a v1.x schema, found {version!r}")

    schema = hitl.get("inputs", {}).get("schema", {})
    fields = schema.get("fields")
    outcomes = schema.get("outcomes")
    if not isinstance(fields, list) or not fields:
        fail("HITL schema must define fields")
    if not isinstance(outcomes, list) or not outcomes:
        fail("HITL schema must define outcomes")

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

    reason_keywords = ("reason", "comment", "explanation", "justification", "note")
    if not any(
        f.get("direction") in {"output", "inOut"}
        and f.get("type") in {"text", "string", "textarea"}
        and any(kw in field_text(f, "id") or kw in field_text(f, "label") for kw in reason_keywords)
        for f in fields
    ):
        fail("HITL must expose a text output field for the rejection reason (e.g., reason, comment)")

    input_bindings = [
        f.get("binding", "")
        for f in fields
        if f.get("direction") in {"input", "inOut"} and isinstance(f.get("binding"), str)
    ]
    if not input_bindings:
        fail("HITL input fields must be bound to upstream script output")
    if not any(is_upstream_output_binding(binding) for binding in input_bindings):
        fail(
            "HITL input bindings must use vars.<node>.output.<field> "
            "or =js:$vars.<node>.output.<field>"
        )

    # The task's own prompt asks for approve/reject review and a downstream log
    # step; it does not prescribe HOW the task exits, and the SDK offers two
    # shapes that are both correct:
    #
    #   * the base node's 1.0 definition (and every variant: quick-form,
    #     action-app, document-validation) declares one source handle,
    #     `completed`;
    #   * `outcomePorts: true` / `exposeError: true` select the base node's
    #     1.1/1.2 definition, whose ONLY source handle is `outcome-{item.id}`
    #     repeated over the outcomes. There is no `completed` handle there, and
    #     an edge to one is refused by `uip maestro flow validate` as an
    #     undeclared source handle.
    #
    # This gate used to require `completed` (or the `outcome-completed` special
    # case added in #1477, which only helps when an outcome is literally NAMED
    # "Completed"). An agent that took the second shape therefore failed a task
    # it had satisfied — flow-builder-sdk#718, where the same task scored 1.0 the
    # run before because the agent happened to pick the first shape. What the
    # gate means to assert is that the review CONTINUES somewhere, so assert
    # that.
    exit_ports = {
        str(e.get("sourcePort") or "")
        for e in edges
        if e.get("sourceNodeId") == hitl_id
    }
    if not (
        "completed" in exit_ports
        or any(port.startswith("outcome-") for port in exit_ports)
    ):
        fail(
            "HITL completion must be wired: an edge on the 'completed' handle, or "
            "per-outcome edges ('outcome-<id>') when outcomePorts/exposeError is used. "
            f"Found {sorted(exit_ports) or 'no outgoing edges'}"
        )

    scripts = [
        str(n.get("inputs", {}).get("script", ""))
        for n in nodes
        if n.get("type") == "core.action.script"
    ]
    expected_output_path = f"$vars.{hitl_id}.output"
    if not any(expected_output_path in script for script in scripts):
        fail(f"Downstream script must read HITL output via {expected_output_path}")

    print(
        f"OK: HITL node {hitl_id} uses a v1.x schema, captures approval + reason, "
        f"continues on {sorted(exit_ports)}, and uses .output paths"
    )


if __name__ == "__main__":
    main()
