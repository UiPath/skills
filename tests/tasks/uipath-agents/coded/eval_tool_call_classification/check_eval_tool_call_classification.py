#!/usr/bin/env python3
"""Validate coded-agent eval configs for tool-call and classification types."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("eval-matrix")

EXPECTED_TYPES = {
    "uipath-llm-judge-output-strict-json-similarity",
    "uipath-llm-judge-trajectory-simulation",
    "uipath-tool-call-order",
    "uipath-tool-call-args",
    "uipath-tool-call-count",
    "uipath-tool-call-output",
    "uipath-binary-classification",
    "uipath-multiclass-classification",
}

CRITERIA_KEYS = {
    "uipath-llm-judge-output-strict-json-similarity": "expectedOutput",
    "uipath-llm-judge-trajectory-simulation": "expectedAgentBehavior",
    "uipath-tool-call-order": "toolCallsOrder",
    "uipath-tool-call-args": "toolCalls",
    "uipath-tool-call-count": "toolCallsCount",
    "uipath-tool-call-output": "toolOutputs",
    "uipath-binary-classification": "expectedClass",
    "uipath-multiclass-classification": "expectedClass",
}


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{path} should contain a JSON object")
    return value


def main() -> None:
    if not ROOT.is_dir():
        fail(f"project directory {ROOT} does not exist")

    eval_dir = ROOT / "evaluations" / "evaluators"
    set_dir = ROOT / "evaluations" / "eval-sets"
    if not eval_dir.is_dir():
        fail(f"{eval_dir} does not exist")
    if not set_dir.is_dir():
        fail(f"{set_dir} does not exist")

    ids_by_type: dict[str, str] = {}
    for path in sorted(eval_dir.glob("*.json")):
        doc = load(path)
        type_id = doc.get("evaluatorTypeId")
        eval_id = doc.get("id")
        if type_id in EXPECTED_TYPES:
            if not eval_id:
                fail(f"{path} has expected type {type_id} but no id")
            ids_by_type[type_id] = eval_id
            cfg = doc.get("evaluatorConfig") or {}
            if type_id.startswith("uipath-llm-judge") and not cfg.get("model"):
                fail(f"{path} LLM evaluator is missing evaluatorConfig.model")

    missing = EXPECTED_TYPES - set(ids_by_type)
    if missing:
        fail(f"missing evaluator type(s): {sorted(missing)}")
    print(f"OK: evaluator files cover all expected types: {sorted(ids_by_type)}")

    set_files = sorted(set_dir.glob("*.json"))
    if not set_files:
        fail(f"no eval set files in {set_dir}")
    eval_set = load(set_files[0])
    if eval_set.get("version") != "1.0":
        fail(f'eval set version should be "1.0", got {eval_set.get("version")!r}')
    refs = set(eval_set.get("evaluatorRefs") or [])
    missing_refs = set(ids_by_type.values()) - refs
    if missing_refs:
        fail(f"eval set is missing evaluatorRefs: {sorted(missing_refs)}")

    cases = eval_set.get("evaluations") or []
    if not cases:
        fail("eval set has no evaluations")
    criteria_blob = json.dumps([c.get("evaluationCriterias") for c in cases], sort_keys=True)
    for type_id, eval_id in ids_by_type.items():
        if eval_id not in criteria_blob:
            fail(f"evaluationCriterias never references evaluator id {eval_id!r}")
        required_key = CRITERIA_KEYS[type_id]
        if required_key not in criteria_blob:
            fail(f"criteria for {type_id} should contain {required_key!r}")

    print(
        f"OK: eval set references {len(ids_by_type)} evaluator ids and "
        "contains the expected criteria keys"
    )


if __name__ == "__main__":
    main()

