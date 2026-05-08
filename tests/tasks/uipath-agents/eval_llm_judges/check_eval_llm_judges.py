#!/usr/bin/env python3
"""Eval-lifecycle check for the LLM-judge path (two evaluators).

Validates the dual-evaluator harness:
  - `LLMJudgeOutputEvaluator` config with the
    `uipath-llm-judge-output-semantic-similarity` typeId.
  - `LLMJudgeTrajectoryEvaluator` config with the
    `uipath-llm-judge-trajectory-similarity` typeId.
  - One eval set whose `evaluatorRefs` lists BOTH ids and whose test
    cases key `evaluationCriterias` on BOTH ids — the output judge
    gets an `expectedOutput` block, the trajectory judge gets an
    `expectedAgentBehavior` string.
  - `eval-results.json` exists and is a non-empty test-case list.
    LLM-judge scores are continuous (0.0-1.0) so we don't assert an
    exact score — only that the results file is well-formed and
    references the expected evaluator ids.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("intent-classifier")

EXPECTED_EVALUATORS = {
    "LLMJudgeOutputEvaluator": "uipath-llm-judge-output-semantic-similarity",
    "LLMJudgeTrajectoryEvaluator": "uipath-llm-judge-trajectory-similarity",
}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_evaluator_configs() -> None:
    evaluators_dir = ROOT / "evaluations" / "evaluators"
    if not evaluators_dir.is_dir():
        sys.exit(f"FAIL: {evaluators_dir} does not exist")
    found_by_id: dict[str, Path] = {}
    for json_file in sorted(evaluators_dir.glob("*.json")):
        doc = _load_json(json_file)
        eval_id = doc.get("id")
        type_id = doc.get("evaluatorTypeId")
        if eval_id in EXPECTED_EVALUATORS:
            expected_type = EXPECTED_EVALUATORS[eval_id]
            if type_id != expected_type:
                sys.exit(
                    f'FAIL: evaluator {eval_id!r} should have evaluatorTypeId='
                    f'{expected_type!r}, got {type_id!r}'
                )
            found_by_id[eval_id] = json_file
            print(f'OK: evaluator config {json_file.name} has id={eval_id!r} typeId={type_id!r}')
    missing = set(EXPECTED_EVALUATORS) - set(found_by_id)
    if missing:
        sys.exit(
            f'FAIL: missing evaluator configs for ids {sorted(missing)}. '
            f'Found ids: {sorted(found_by_id)}'
        )


def check_eval_set() -> None:
    eval_sets_dir = ROOT / "evaluations" / "eval-sets"
    if not eval_sets_dir.is_dir():
        sys.exit(f"FAIL: {eval_sets_dir} does not exist")
    files = sorted(eval_sets_dir.glob("*.json"))
    if not files:
        sys.exit(f"FAIL: no eval set files in {eval_sets_dir}")
    if len(files) > 1:
        sys.exit(f"FAIL: expected exactly one eval set file, got {len(files)}")
    path = files[0]
    doc = _load_json(path)
    if doc.get("version") != "1.0":
        sys.exit(f'FAIL: eval set version should be "1.0", got {doc.get("version")!r}')
    refs = doc.get("evaluatorRefs") or []
    missing_refs = set(EXPECTED_EVALUATORS) - set(refs)
    if missing_refs:
        sys.exit(
            f'FAIL: eval set `evaluatorRefs` is missing {sorted(missing_refs)}. '
            f'Got: {refs}'
        )
    cases = doc.get("evaluations") or []
    if len(cases) < 2:
        sys.exit(f"FAIL: eval set must have at least 2 test cases, got {len(cases)}")
    for i, case in enumerate(cases):
        crit = case.get("evaluationCriterias") or {}
        for evaluator_id in EXPECTED_EVALUATORS:
            if evaluator_id not in crit:
                sys.exit(
                    f'FAIL: test case {i} (`{case.get("id", "?")}`) does not '
                    f'key evaluationCriterias on {evaluator_id!r}. Got keys: '
                    f'{list(crit.keys())}'
                )
        # Trajectory judge requires `expectedAgentBehavior`.
        traj = crit.get("LLMJudgeTrajectoryEvaluator") or {}
        if not traj.get("expectedAgentBehavior"):
            sys.exit(
                f'FAIL: test case {i} LLMJudgeTrajectoryEvaluator entry is '
                f'missing the required `expectedAgentBehavior` field. Got: {traj}'
            )
        # Output judge requires `expectedOutput`.
        out = crit.get("LLMJudgeOutputEvaluator") or {}
        if "expectedOutput" not in out:
            sys.exit(
                f'FAIL: test case {i} LLMJudgeOutputEvaluator entry is '
                f'missing the required `expectedOutput` field. Got: {out}'
            )
    print(
        f"OK: eval set {path.name} references both judges across {len(cases)} "
        "test cases with the right per-judge criteria"
    )


def check_results() -> None:
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
    seen_ids: set[str] = set()
    for c in cases:
        if not isinstance(c, dict):
            continue
        for r in c.get("evaluationRunResults") or []:
            if isinstance(r, dict):
                eid = r.get("evaluatorId")
                if eid:
                    seen_ids.add(eid)
    missing = set(EXPECTED_EVALUATORS) - seen_ids
    if missing:
        sys.exit(
            f'FAIL: results file does not surface evaluatorId entries for '
            f'{sorted(missing)} (seen: {sorted(seen_ids)}). Both judges '
            f'should run on every test case.'
        )
    print(
        f"OK: results file references both evaluator ids ({sorted(seen_ids)}) "
        f"across {len(cases)} test case(s)"
    )


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_evaluator_configs()
    check_eval_set()
    check_results()


if __name__ == "__main__":
    main()
