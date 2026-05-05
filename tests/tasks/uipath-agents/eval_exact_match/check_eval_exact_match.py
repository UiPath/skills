#!/usr/bin/env python3
"""Eval-lifecycle check for the deterministic ExactMatch path.

Validates that the agent authored both halves of the evaluation
harness — the evaluator config under `evaluations/evaluators/` AND
the evaluation set under `evaluations/eval-sets/` whose `evaluatorRefs`
match the evaluator `id` — and that `uip codedagent eval --no-report`
produced an output file in which every test case has
`status == "PASSED"` (deterministic agent + deterministic evaluator
means anything else is a bug).

Checks:
  1. `adder/evaluations/evaluators/<file>.json` has `evaluatorTypeId`
     == "uipath-exact-match" and a non-empty `id`.
  2. `adder/evaluations/eval-sets/<file>.json` has version "1.0",
     `evaluatorRefs` referencing the evaluator id, at least 2 test
     cases, and each test case's `evaluationCriterias` keys the
     evaluator id.
  3. `eval-results.json` exists with the documented top-level shape
     (`evaluationSetName`, `evaluationSetResults: [...]`), every
     test case in `evaluationSetResults` has at least one matching
     `evaluationRunResults[]` entry for the configured evaluator,
     and every such entry scored exactly 1.0 (deterministic agent +
     deterministic evaluator: anything below 1.0 is a bug).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("adder")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_single_json(directory: Path) -> Path:
    if not directory.is_dir():
        sys.exit(f"FAIL: {directory} does not exist")
    files = sorted(p for p in directory.glob("*.json") if p.is_file())
    if not files:
        sys.exit(f"FAIL: {directory} contains no .json files")
    if len(files) > 1:
        sys.exit(f"FAIL: {directory} should contain exactly one .json file, got {len(files)}")
    return files[0]


def check_evaluator() -> str:
    path = find_single_json(ROOT / "evaluations" / "evaluators")
    doc = _load_json(path)
    type_id = doc.get("evaluatorTypeId")
    if type_id != "uipath-exact-match":
        sys.exit(
            f'FAIL: {path.name} evaluatorTypeId should be "uipath-exact-match", '
            f'got {type_id!r}'
        )
    eval_id = doc.get("id")
    if not eval_id:
        sys.exit(f"FAIL: {path.name} is missing required `id` field")
    print(f'OK: evaluator config {path.name} has evaluatorTypeId={type_id!r} id={eval_id!r}')
    return eval_id


def check_eval_set(evaluator_id: str) -> int:
    path = find_single_json(ROOT / "evaluations" / "eval-sets")
    doc = _load_json(path)
    if doc.get("version") != "1.0":
        sys.exit(f'FAIL: eval set version should be "1.0", got {doc.get("version")!r}')
    refs = doc.get("evaluatorRefs") or []
    if evaluator_id not in refs:
        sys.exit(
            f'FAIL: eval set `evaluatorRefs` does not include the evaluator '
            f'id {evaluator_id!r}. Got: {refs}'
        )
    cases = doc.get("evaluations") or []
    if len(cases) < 2:
        sys.exit(f"FAIL: eval set must have at least 2 test cases, got {len(cases)}")
    for i, case in enumerate(cases):
        crit = case.get("evaluationCriterias") or {}
        if evaluator_id not in crit:
            sys.exit(
                f'FAIL: eval set test case {i} (`{case.get("id", "?")}`) does '
                f'not key its evaluationCriterias on the evaluator id '
                f'{evaluator_id!r}. Got keys: {list(crit.keys())}'
            )
    print(f'OK: eval set {path.name} references {evaluator_id!r} across {len(cases)} test cases')
    return len(cases)


def check_results(evaluator_id: str, expected_case_count: int) -> None:
    path = ROOT / "eval-results.json"
    doc = _load_json(path)
    if not isinstance(doc, dict):
        sys.exit(f"FAIL: {path.name} top-level should be an object, got {type(doc).__name__}")
    cases = doc.get("evaluationSetResults")
    if not isinstance(cases, list) or not cases:
        sys.exit(
            f"FAIL: {path.name} is missing a non-empty `evaluationSetResults` "
            f"list. Top-level keys: {list(doc.keys())}"
        )
    if len(cases) != expected_case_count:
        sys.exit(
            f"FAIL: expected {expected_case_count} entries in "
            f"`evaluationSetResults` (one per eval-set test case), got {len(cases)}"
        )
    print(f'OK: eval-results.json carries {len(cases)} entries in evaluationSetResults')
    bad_cases = []
    matching_run_count = 0
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_name = case.get("evaluationName") or "?"
        runs = case.get("evaluationRunResults") or []
        matching = [
            r for r in runs
            if isinstance(r, dict) and r.get("evaluatorId") == evaluator_id
        ]
        if not matching:
            bad_cases.append(
                f'{case_name!r}: no evaluationRunResults entry references '
                f'evaluatorId={evaluator_id!r}'
            )
            continue
        for r in matching:
            score = (r.get("result") or {}).get("score")
            if score != 1.0:
                bad_cases.append(
                    f'{case_name!r}: evaluator {evaluator_id!r} scored '
                    f'{score!r}, expected 1.0 (deterministic agent + '
                    f'deterministic evaluator)'
                )
        matching_run_count += len(matching)
    if bad_cases:
        sys.exit("FAIL: " + " | ".join(bad_cases))
    print(
        f'OK: every test case has an ExactMatchEvaluator run scoring 1.0 '
        f'({matching_run_count} run(s) across {len(cases)} case(s))'
    )


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    evaluator_id = check_evaluator()
    case_count = check_eval_set(evaluator_id)
    check_results(evaluator_id, case_count)


if __name__ == "__main__":
    main()
