"""Reusable LangGraph project assertions for coded-agent check scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def assert_langgraph_config(root: Path, module: Path) -> None:
    """Assert `langgraph.json` points at the exported graph module."""
    path = root / "langgraph.json"
    if not path.is_file():
        sys.exit(f"FAIL: missing LangGraph config at {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"FAIL: {path} is not valid JSON: {exc}")

    graphs = data.get("graphs")
    if not isinstance(graphs, dict) or not graphs:
        sys.exit("FAIL: langgraph.json must contain a non-empty `graphs` object")

    expected_targets = {f"./{module.name}:graph", f"{module.name}:graph"}
    if not any(target in expected_targets for target in graphs.values()):
        sys.exit(
            "FAIL: langgraph.json must map a graph entry to the exported graph "
            f"({', '.join(sorted(expected_targets))}); got {graphs!r}"
        )
    print(f"OK: langgraph.json registers {module.name}:graph")
