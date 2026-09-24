#!/usr/bin/env python3
"""Verify Flow eval simulation side effects."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path("EvalSim")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load_jsons(root: Path) -> list[tuple[Path, Any]]:
    docs: list[tuple[Path, Any]] = []
    for path in root.rglob("*.json"):
        try:
            docs.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    return docs


def walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def component_id(sim: dict) -> str:
    for key in ("componentId", "componentID", "component", "id"):
        value = sim.get(key)
        if value:
            return str(value)
    return json.dumps(sim, sort_keys=True)


def strategy(sim: dict) -> str:
    value = sim.get("strategy") or sim.get("simulationStrategy") or sim.get("type")
    return str(value)


def main() -> None:
    if not ROOT.is_dir():
        fail(f"{ROOT} directory does not exist")
    docs = load_jsons(ROOT)
    if not docs:
        fail(f"no JSON files found under {ROOT}")

    eval_sets = [
        (p, d)
        for p, d in docs
        if isinstance(d, dict)
        and d.get("name") == "Simulation Set"
        and isinstance(d.get("evaluations"), list)
    ]
    if not eval_sets:
        fail('no eval set named "Simulation Set" found')
    set_path, eval_set = eval_sets[0]

    cases = eval_set.get("evaluations") or []
    case = next((c for c in cases if isinstance(c, dict) and c.get("name") == "customer-lookup"), None)
    if not case:
        fail(f"{set_path} has no data point named customer-lookup")

    simulations = [
        item
        for item in walk(case)
        if isinstance(item, dict)
        and any(k in item for k in ("componentId", "componentID", "component"))
        and any(k in item for k in ("strategy", "simulationStrategy", "mockValue", "mock-value"))
    ]
    if not simulations:
        fail(f"data point customer-lookup has no simulations. Keys: {list(case.keys())}")

    lookup = [s for s in simulations if component_id(s) == "lookupCustomer"]
    if len(lookup) != 1:
        fail(f"expected exactly one overwritten lookupCustomer simulation, got {len(lookup)}")
    if "static" not in strategy(lookup[0]).lower():
        fail(f"lookupCustomer simulation should be Static, got {strategy(lookup[0])!r}")

    draft = [s for s in simulations if component_id(s) == "draftEmail"]
    if draft:
        fail("draftEmail simulation should have been removed, but it remains in the eval set")

    print(
        "OK: simulation data point has one Static lookupCustomer simulation "
        "after overwrite and removed draftEmail simulation"
    )


if __name__ == "__main__":
    main()
