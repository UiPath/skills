#!/usr/bin/env python3
"""Verify low-code `uip agent eval` local CRUD artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path("EvalLowCodeSol") / "EvalLowCodeAgent"
EXPECTED_TYPES = {1, 5, 6, 7}
DISPLAY_NAMES = {
    "Default Evaluator",
    "Default Trajectory Evaluator",
    "semantic-similarity",
    "trajectory",
    "exact match",
    "json similarity",
}


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def main() -> None:
    if not ROOT.is_dir():
        fail(f"agent project {ROOT} does not exist")
    eval_dir = ROOT / "evals" / "evaluators"
    set_dir = ROOT / "evals" / "eval-sets"
    if not eval_dir.is_dir():
        fail(f"{eval_dir} does not exist")
    if not set_dir.is_dir():
        fail(f"{set_dir} does not exist")

    evaluators: dict[str, dict] = {}
    types: set[int] = set()
    for path in sorted(eval_dir.glob("*.json")):
        doc = load(path)
        if not isinstance(doc, dict):
            continue
        eval_id = doc.get("id")
        etype = doc.get("type")
        category = doc.get("category")
        if eval_id:
            evaluators[eval_id] = doc
        if isinstance(etype, int):
            types.add(etype)
        if etype in (5, 7) and not doc.get("model"):
            fail(f"{path} LLM/trajectory evaluator is missing model")
        if etype in (1, 6) and category != 0:
            fail(f"{path} deterministic evaluator should use category 0, got {category!r}")

    missing_types = EXPECTED_TYPES - types
    if missing_types:
        fail(f"missing low-code evaluator type(s): {sorted(missing_types)}")
    print(f"OK: evaluator directory covers low-code types {sorted(types & EXPECTED_TYPES)}")

    eval_sets = []
    for path in sorted(set_dir.glob("*.json")):
        doc = load(path)
        if isinstance(doc, dict) and doc.get("name") == "Regression Eval":
            eval_sets.append((path, doc))
    if not eval_sets:
        fail('no eval set named "Regression Eval" found')
    set_path, eval_set = eval_sets[0]

    refs = eval_set.get("evaluatorRefs") or []
    if len(refs) < 4:
        fail(f"{set_path} should reference at least 4 evaluators, got {refs!r}")
    missing_refs = [ref for ref in refs if ref not in evaluators]
    if missing_refs:
        fail(f"eval set references ids without evaluator files: {missing_refs!r}")
    bad_name_refs = [ref for ref in refs if ref in DISPLAY_NAMES or ref.endswith(".json")]
    if bad_name_refs:
        fail(f"eval set should reference evaluator UUID ids, not names/files: {bad_name_refs!r}")

    cases = eval_set.get("evaluations") or []
    if len(cases) < 2:
        fail(f"expected at least 2 test cases, got {len(cases)}")
    blob = json.dumps(cases, sort_keys=True)
    required = [
        "expectedOutput",
        "expectedAgentBehavior",
        "simulationInstructions",
        "simulateInput",
        "simulateTools",
        "inputGenerationInstructions",
        "evalSetId",
        "manual",
    ]
    for key in required:
        if key not in blob:
            fail(f"test cases should contain {key!r}")

    print(
        f"OK: {set_path} references evaluator UUIDs and has {len(cases)} "
        "test cases with output, behavior, simulation, and evalSetId fields"
    )


if __name__ == "__main__":
    main()

