#!/usr/bin/env python3
"""Check template-first discovery: a new Portland flow mirrors the seeded weather flow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path("BellevueWeather") / "BellevueWeather"
SOURCE_FLOW = PROJECT_DIR / "BellevueWeather.flow"
TARGET_FLOW = PROJECT_DIR / "PortlandWeather.flow"


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        _fail(f"{path} does not exist")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        _fail(f"{path} is not valid JSON: {exc}")


def _node_type_counts(flow: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    nodes = flow.get("nodes")
    if not isinstance(nodes, list):
        _fail("flow nodes must be a list")
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type") or "")
        counts[node_type] = counts.get(node_type, 0) + 1
    return counts


def _edge_pairs(flow: dict[str, Any]) -> set[tuple[str, str]]:
    edges = flow.get("edges")
    if not isinstance(edges, list):
        _fail("flow edges must be a list")
    pairs: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = str(edge.get("sourceNodeId") or "")
        target = str(edge.get("targetNodeId") or "")
        if source and target:
            pairs.add((source, target))
    return pairs


def _find_nodes(flow: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return [
        node
        for node in flow.get("nodes") or []
        if isinstance(node, dict) and node.get("type") == node_type
    ]


def _json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def main() -> None:
    source = _load_json(SOURCE_FLOW)
    target = _load_json(TARGET_FLOW)

    if "PortlandWeather" not in str(target.get("name", "")):
        _fail("new flow name should be PortlandWeather")

    source_counts = _node_type_counts(source)
    target_counts = _node_type_counts(target)
    expected_types = {
        "core.trigger.manual": 1,
        "core.action.http": 1,
        "core.action.script": 1,
        "core.logic.decision": 1,
        "core.control.end": 2,
    }
    for node_type, expected_count in expected_types.items():
        if target_counts.get(node_type) != expected_count:
            _fail(
                f"expected {expected_count} {node_type} node(s), "
                f"found {target_counts.get(node_type, 0)}; all counts={target_counts}"
            )
        if source_counts.get(node_type) != expected_count:
            _fail(f"seed Bellevue flow was mutated for node type {node_type}: {source_counts}")

    expected_edges = {
        ("start", "getWeather"),
        ("getWeather", "formatSummary"),
        ("formatSummary", "checkTemperature"),
        ("checkTemperature", "endNiceDay"),
        ("checkTemperature", "endBringJacket"),
    }
    if not expected_edges.issubset(_edge_pairs(target)):
        _fail(f"new flow does not preserve weather-template edges; found {_edge_pairs(target)}")

    http_nodes = _find_nodes(target, "core.action.http")
    http_text = _json_text(http_nodes[0]).lower()
    for needle in ("open-meteo.com", "45.5152", "-122.6784"):
        if needle not in http_text:
            _fail(f"new HTTP node does not target Portland Open-Meteo data: missing {needle}")
    for stale in ("47.6101", "-122.2015"):
        if stale in http_text:
            _fail(f"new HTTP node still uses Bellevue coordinate {stale}")

    target_text = _json_text(target).lower()
    if "portland" not in target_text:
        _fail("new flow should mention Portland in labels or summary output")
    if "nice day" not in target_text or "bring a jacket" not in target_text:
        _fail("new flow should preserve the template branch outputs")

    source_text = _json_text(source).lower()
    if "bellevue" not in source_text or "portland" in source_text:
        _fail("BellevueWeather.flow should remain the Bellevue template")

    print("OK: PortlandWeather.flow mirrors the local Bellevue template and keeps BellevueWeather.flow unchanged")


if __name__ == "__main__":
    main()
