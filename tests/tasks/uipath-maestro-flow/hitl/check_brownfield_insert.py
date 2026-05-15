#!/usr/bin/env python3
"""Brownfield HITL insert: validate the flow and insertion invariants."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def find_flow() -> Path:
    matches = sorted(Path.cwd().glob("**/ContractReview.flow"))
    if not matches:
        fail(f"No ContractReview.flow found under {Path.cwd()}")
    if len(matches) > 1:
        joined = "\n  - ".join(str(path) for path in matches)
        fail(
            "Multiple ContractReview.flow files found; refusing to guess:"
            f"\n  - {joined}"
        )
    return matches[0]


def validate_flow(path: Path) -> None:
    result = subprocess.run(
        ["uip", "maestro", "flow", "validate", str(path), "--output", "json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        fail(
            f"uip maestro flow validate failed for {path}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


def load_flow(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def has_edge(
    edges: list[dict],
    source: str,
    target: str,
    source_ports: set[str] | None = None,
) -> bool:
    for edge in edges:
        if edge.get("sourceNodeId") != source or edge.get("targetNodeId") != target:
            continue
        if source_ports is None or edge.get("sourcePort") in source_ports:
            return True
    return False


def main() -> None:
    path = find_flow()
    validate_flow(path)
    flow = load_flow(path)

    nodes = flow.get("nodes")
    edges = flow.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        fail("Flow must contain nodes[] and edges[]")

    nodes_by_id = {node.get("id"): node for node in nodes if node.get("id")}
    if "extractMeta" not in nodes_by_id:
        fail("Original script node 'extractMeta' is missing")
    if "end" not in nodes_by_id:
        fail("End node 'end' is missing")

    hitl_nodes = [
        node for node in nodes if node.get("type") == "uipath.human-in-the-loop"
    ]
    if len(hitl_nodes) != 1:
        fail(
            "Expected exactly one uipath.human-in-the-loop node, "
            f"found {len(hitl_nodes)}"
        )
    hitl = hitl_nodes[0]
    hitl_id = hitl.get("id")
    if not hitl_id:
        fail("HITL node is missing id")

    if has_edge(edges, "extractMeta", "end"):
        fail("Original extractMeta -> End edge must be removed")
    if not has_edge(edges, "extractMeta", hitl_id, {"output", "success"}):
        fail("extractMeta must be wired into the inserted HITL node")
    if not has_edge(edges, hitl_id, "end", {"completed"}):
        fail("HITL completed handle must be wired to End")

    schema = hitl.get("inputs", {}).get("schema", {})
    fields = schema.get("fields")
    if not isinstance(fields, list) or not fields:
        fail("HITL schema must define fields")
    if not any(
        field.get("direction") in {"output", "inOut"} and field.get("type") == "boolean"
        for field in fields
    ):
        fail("HITL schema must include a boolean reviewer output field")

    print(
        "OK: ContractReview.flow validates and preserves extractMeta -> HITL "
        "-> completed -> End with a boolean reviewer output"
    )


if __name__ == "__main__":
    main()
