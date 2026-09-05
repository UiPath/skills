#!/usr/bin/env python3
"""Eval-lifecycle check for the LLM-judge path (two evaluators).

Validates the dual-evaluator harness by `evaluatorTypeId`, not by
evaluator `id` — the skill documents the `id` as a free placeholder
(`<EvaluatorId>`), so agents may pick any self-consistent name:
  - Exactly one OUTPUT judge config: `evaluatorTypeId` in
    `OUTPUT_JUDGE_TYPES` (semantic-similarity or strict-json-similarity
    — both are documented LLM output judges; strict-json is the
    documented fit for structured outputs like this fixture's).
  - Exactly one TRAJECTORY judge config: `evaluatorTypeId` in
    `TRAJECTORY_JUDGE_TYPES`.
  - One eval set whose `evaluatorRefs` lists BOTH discovered ids and
    whose test cases key `evaluationCriterias` on BOTH ids — the
    output judge gets an `expectedOutput` block, the trajectory judge
    gets an `expectedAgentBehavior` string.
  - `eval-results.json` exists and is a non-empty test-case list.
    LLM-judge scores are continuous (0.0-1.0) so we don't assert an
    exact score — only that the results file is well-formed and
    references both discovered evaluator ids.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-agents")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("intent-classifier")

OUTPUT_JUDGE_TYPES = {
    "uipath-llm-judge-output-semantic-similarity",
    "uipath-llm-judge-output-strict-json-similarity",
}
TRAJECTORY_JUDGE_TYPES = {
    "uipath-llm-judge-trajectory-similarity",
    "uipath-llm-judge-trajectory-simulation",
}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_evaluator_configs() -> dict[str, str]:
    """Resolve the two judges by typeId; return {'output': id, 'trajectory': id}."""
    evaluators_dir = ROOT / "evaluations" / "evaluators"
    if not evaluators_dir.is_dir():
        sys.exit(f"FAIL: {evaluators_dir} does not exist")
    found: dict[str, list[tuple[str, Path]]] = {"output": [], "trajectory": []}
    for json_file in sorted(evaluators_dir.glob("*.json")):
        doc = _load_json(json_file)
        type_id = doc.get("evaluatorTypeId")
        if type_id in OUTPUT_JUDGE_TYPES:
            kind = "output"
        elif type_id in TRAJECTORY_JUDGE_TYPES:
            kind = "trajectory"
        else:
            continue
        eval_id = doc.get("id")
        if not eval_id or not isinstance(eval_id, str):
            sys.exit(
                f'FAIL: {json_file.name} has evaluatorTypeId={type_id!r} but '
                f'no string `id` field. Got: {eval_id!r}'
            )
        found[kind].append((eval_id, json_file))
        print(
            f'OK: evaluator config {json_file.name} is the {kind} judge '
            f'(id={eval_id!r}, typeId={type_id!r})'
        )
    ids: dict[str, str] = {}
    for kind, types in (("output", OUTPUT_JUDGE_TYPES), ("trajectory", TRAJECTORY_JUDGE_TYPES)):
        matches = found[kind]
        if not matches:
            sys.exit(
                f'FAIL: no {kind}-judge evaluator config in {evaluators_dir} — '
                f'expected exactly one file with `evaluatorTypeId` in '
                f'{sorted(types)}'
            )
        if len(matches) > 1:
            sys.exit(
                f'FAIL: expected exactly one {kind}-judge evaluator config, '
                f'got {len(matches)}: {sorted(p.name for _, p in matches)}'
            )
        ids[kind] = matches[0][0]
    if ids["output"] == ids["trajectory"]:
        sys.exit(
            f'FAIL: output and trajectory judges share the same id '
            f'{ids["output"]!r} — evaluator ids must be unique'
        )
    return ids


def check_eval_set(ids: dict[str, str]) -> None:
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
    missing_refs = set(ids.values()) - set(refs)
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
        for evaluator_id in ids.values():
            if evaluator_id not in crit:
                sys.exit(
                    f'FAIL: test case {i} (`{case.get("id", "?")}`) does not '
                    f'key evaluationCriterias on {evaluator_id!r}. Got keys: '
                    f'{list(crit.keys())}'
                )
        # Trajectory judge requires `expectedAgentBehavior`.
        traj = crit.get(ids["trajectory"]) or {}
        if not traj.get("expectedAgentBehavior"):
            sys.exit(
                f'FAIL: test case {i} trajectory-judge entry ({ids["trajectory"]!r}) '
                f'is missing the required `expectedAgentBehavior` field. Got: {traj}'
            )
        # Output judge requires `expectedOutput`.
        out = crit.get(ids["output"]) or {}
        if "expectedOutput" not in out:
            sys.exit(
                f'FAIL: test case {i} output-judge entry ({ids["output"]!r}) '
                f'is missing the required `expectedOutput` field. Got: {out}'
            )
    print(
        f"OK: eval set {path.name} references both judges across {len(cases)} "
        "test cases with the right per-judge criteria"
    )


def check_results(ids: dict[str, str]) -> None:
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
    missing = set(ids.values()) - seen_ids
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
    ids = check_evaluator_configs()
    check_eval_set(ids)
    check_results(ids)


if __name__ == "__main__":
    main()
