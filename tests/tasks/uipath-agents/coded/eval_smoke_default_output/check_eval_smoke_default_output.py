#!/usr/bin/env python3
"""Eval-lifecycle check: greenfield smoke-evaluator default must be output-based.

A plain single-LLM-call agent (`summarizer`) with no @traced spans and no tool
calls has no meaningful execution trajectory. A trajectory or tool-call
evaluator scores against emitted spans / AgentRunHistory and returns 0.0 on
such an agent even when it runs perfectly — so the skill must NOT default the
smoke evaluator to one of those. The correct default is output-based:
semantic-similarity for natural-language output, or a deterministic
exact-match / contains / json-similarity evaluator.

Checks:
  1. `summarizer/evaluations/evaluators/<file>.json` has a non-empty `id` and
     an `evaluatorTypeId` in the allowed OUTPUT-based set.
  2. NO evaluator config under `evaluations/evaluators/` uses a trajectory or
     tool-call `evaluatorTypeId`.
  3. The eval set's `evaluatorRefs` reference the output-based evaluator id,
     it has >= 2 test cases, and each case keys its `evaluationCriterias` on
     that id and carries `expectedOutput` (not `expectedAgentBehavior`).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("summarizer")

OUTPUT_BASED_TYPES = {
    "uipath-llm-judge-output-semantic-similarity",
    "uipath-llm-judge-output-strict-json-similarity",
    "uipath-exact-match",
    "uipath-contains",
    "uipath-json-similarity",
}

FORBIDDEN_TYPE_PREFIXES = (
    "uipath-llm-judge-trajectory",
    "uipath-tool-call",
)


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def _is_forbidden(type_id: str) -> bool:
    return any(type_id.startswith(p) for p in FORBIDDEN_TYPE_PREFIXES)


def check_evaluators() -> str:
    directory = ROOT / "evaluations" / "evaluators"
    if not directory.is_dir():
        sys.exit(f"FAIL: {directory} does not exist")
    files = sorted(p for p in directory.glob("*.json") if p.is_file())
    if not files:
        sys.exit(f"FAIL: {directory} contains no evaluator .json files")

    output_based_id = None
    for path in files:
        doc = _load_json(path)
        type_id = doc.get("evaluatorTypeId")
        if _is_forbidden(type_id or ""):
            sys.exit(
                f"FAIL: {path.name} uses a trajectory/tool-call evaluator "
                f"({type_id!r}). A single-step structured-IO agent produces an "
                f"empty AgentRunHistory, so this scores 0.0 on success. The "
                f"smoke evaluator must default to an output-based type."
            )
        if type_id in OUTPUT_BASED_TYPES and doc.get("id"):
            output_based_id = doc["id"]

    if not output_based_id:
        sys.exit(
            f"FAIL: no output-based evaluator found under {directory}. "
            f"Expected one of {sorted(OUTPUT_BASED_TYPES)}."
        )
    print(f"OK: smoke evaluator defaults to output-based type, id={output_based_id!r}; no trajectory/tool-call evaluators present")
    return output_based_id


def check_eval_set(evaluator_id: str) -> None:
    directory = ROOT / "evaluations" / "eval-sets"
    if not directory.is_dir():
        sys.exit(f"FAIL: {directory} does not exist")
    files = sorted(p for p in directory.glob("*.json") if p.is_file())
    if not files:
        sys.exit(f"FAIL: {directory} contains no eval-set .json files")

    # Find the eval set that references our output-based evaluator.
    target = None
    for path in files:
        doc = _load_json(path)
        if evaluator_id in (doc.get("evaluatorRefs") or []):
            target = (path, doc)
            break
    if target is None:
        sys.exit(
            f"FAIL: no eval set references the output-based evaluator id "
            f"{evaluator_id!r} in `evaluatorRefs`."
        )
    path, doc = target

    if doc.get("version") != "1.0":
        sys.exit(f'FAIL: eval set version should be "1.0", got {doc.get("version")!r}')
    cases = doc.get("evaluations") or []
    if len(cases) < 2:
        sys.exit(f"FAIL: eval set must have at least 2 test cases, got {len(cases)}")
    for i, case in enumerate(cases):
        crit = case.get("evaluationCriterias") or {}
        if evaluator_id not in crit:
            sys.exit(
                f'FAIL: eval set test case {i} (`{case.get("id", "?")}`) does '
                f'not key its evaluationCriterias on {evaluator_id!r}. '
                f'Got keys: {list(crit.keys())}'
            )
        entry = crit[evaluator_id] or {}
        if "expectedAgentBehavior" in entry and "expectedOutput" not in entry:
            sys.exit(
                f'FAIL: test case {i} uses `expectedAgentBehavior` (a '
                f'trajectory-evaluator field) on an output-based evaluator. '
                f'Output-based evaluators expect `expectedOutput`.'
            )
        if "expectedOutput" not in entry:
            sys.exit(
                f'FAIL: test case {i} is missing `expectedOutput` for the '
                f'output-based evaluator {evaluator_id!r}.'
            )
    print(f"OK: eval set {path.name} references {evaluator_id!r} across {len(cases)} cases, each with expectedOutput")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    evaluator_id = check_evaluators()
    check_eval_set(evaluator_id)


if __name__ == "__main__":
    main()
