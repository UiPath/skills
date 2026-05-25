#!/usr/bin/env python3
"""Custom evaluator lifecycle check.

Verifies the agent scaffolded a custom evaluator via the CLI, registered
it to produce a JSON spec, wired it into an eval set, and ran it.

Checks:
  1. `evaluations/evaluators/custom/<file>.py` exists.
  2. `evaluations/evaluators/<file>.json` exists with
     `evaluatorSchema` containing `file://` and a non-empty `id`.
  3. `evaluations/evaluators/custom/types/<kebab-class>-types.json` exists.
  4. `evaluations/eval-sets/<file>.json` has version "1.0",
     `evaluatorRefs` referencing the custom evaluator id, at least
     2 test cases, and each test case's `evaluationCriterias` keys
     the evaluator id.
  5. `eval-results.json` exists with `evaluationSetResults` matching
     the expected case count, each case having an `evaluationRunResults`
     entry for the custom evaluator id with score > 0.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("greeter")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_custom_evaluator_py() -> str:
    custom_dir = ROOT / "evaluations" / "evaluators" / "custom"
    if not custom_dir.is_dir():
        sys.exit(f"FAIL: {custom_dir} does not exist — `uip codedagent add evaluator` not run")
    py_files = sorted(custom_dir.glob("*.py"))
    if not py_files:
        sys.exit(f"FAIL: no Python file in {custom_dir}")
    print(f"OK: custom evaluator Python file exists: {py_files[0].name}")
    return py_files[0].stem


def check_custom_evaluator_json() -> str:
    # register writes the spec to evaluations/evaluators/, not evaluations/evaluators/custom/
    evaluators_dir = ROOT / "evaluations" / "evaluators"
    json_files = sorted(f for f in evaluators_dir.glob("*.json") if "file://" in f.read_text())
    if not json_files:
        sys.exit(f"FAIL: no JSON spec with evaluatorSchema in {evaluators_dir} — `uip codedagent register evaluator` not run")
    spec = _load_json(json_files[0])
    schema = spec.get("evaluatorSchema") or ""
    if "file://" not in schema:
        sys.exit(f"FAIL: evaluator JSON spec missing `evaluatorSchema` with `file://` reference. Got: {schema!r}")
    eval_id = spec.get("id")
    if not eval_id:
        sys.exit("FAIL: evaluator JSON spec missing required `id` field")
    type_id = spec.get("evaluatorTypeId") or ""
    if "file://types/" not in type_id:
        sys.exit(f"FAIL: evaluator JSON spec missing `evaluatorTypeId` pointing to types/ dir. Got: {type_id!r}")
    print(f"OK: evaluator JSON spec exists with id={eval_id!r}, evaluatorSchema={schema!r}")
    return eval_id


def check_custom_evaluator_types(evaluator_id: str) -> None:
    # register writes the types schema to evaluations/evaluators/custom/types/
    types_dir = ROOT / "evaluations" / "evaluators" / "custom" / "types"
    if not types_dir.is_dir():
        sys.exit(f"FAIL: {types_dir} does not exist — `uip codedagent register evaluator` not run")
    json_files = sorted(types_dir.glob("*.json"))
    if not json_files:
        sys.exit(f"FAIL: no types JSON in {types_dir}")
    print(f"OK: evaluator types file exists: {json_files[0].name}")


def check_eval_set(evaluator_id: str) -> int:
    eval_sets_dir = ROOT / "evaluations" / "eval-sets"
    if not eval_sets_dir.is_dir():
        sys.exit(f"FAIL: {eval_sets_dir} does not exist")
    json_files = sorted(eval_sets_dir.glob("*.json"))
    if not json_files:
        sys.exit(f"FAIL: no eval set JSON in {eval_sets_dir}")
    doc = _load_json(json_files[0])
    if doc.get("version") != "1.0":
        sys.exit(f'FAIL: eval set version should be "1.0", got {doc.get("version")!r}')
    refs = doc.get("evaluatorRefs") or []
    if evaluator_id not in refs:
        sys.exit(f"FAIL: eval set `evaluatorRefs` does not include {evaluator_id!r}. Got: {refs}")
    cases = doc.get("evaluations") or []
    if len(cases) < 2:
        sys.exit(f"FAIL: eval set must have at least 2 test cases, got {len(cases)}")
    for i, case in enumerate(cases):
        crit = case.get("evaluationCriterias") or {}
        if evaluator_id not in crit:
            sys.exit(
                f"FAIL: test case {i} (`{case.get('id', '?')}`) does not key "
                f"evaluationCriterias on {evaluator_id!r}. Got keys: {list(crit.keys())}"
            )
    print(f"OK: eval set references {evaluator_id!r} across {len(cases)} test cases")
    return len(cases)


def check_results(evaluator_id: str, expected_case_count: int) -> None:
    # agent may write results to cwd or inside the project dir
    path = ROOT / "eval-results.json"
    if not path.is_file():
        path = Path(os.getcwd()) / "eval-results.json"
    doc = _load_json(path)
    cases = doc.get("evaluationSetResults")
    if not isinstance(cases, list) or not cases:
        sys.exit(f"FAIL: eval-results.json missing non-empty `evaluationSetResults`. Keys: {list(doc.keys())}")
    if len(cases) != expected_case_count:
        sys.exit(
            f"FAIL: expected {expected_case_count} result(s) in eval-results.json, got {len(cases)}"
        )
    bad_missing = []
    bad_score = []
    for case in cases:
        runs = case.get("evaluationRunResults") or []
        matching = [r for r in runs if isinstance(r, dict) and r.get("evaluatorId") == evaluator_id]
        if not matching:
            bad_missing.append(case.get("evaluationName") or "?")
        elif not any((r.get("result") or {}).get("score", 0) > 0 for r in matching):
            bad_score.append(case.get("evaluationName") or "?")
    if bad_missing:
        sys.exit(f"FAIL: no evaluationRunResults for {evaluator_id!r} in cases: {bad_missing}")
    if bad_score:
        sys.exit(f"FAIL: custom evaluator scored 0 or missing score in cases: {bad_score}")
    print(f"OK: eval-results.json has {len(cases)} result(s) with custom evaluator runs, all scored > 0")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_custom_evaluator_py()
    evaluator_id = check_custom_evaluator_json()
    check_custom_evaluator_types(evaluator_id)
    case_count = check_eval_set(evaluator_id)
    check_results(evaluator_id, case_count)


if __name__ == "__main__":
    main()
