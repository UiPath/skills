#!/usr/bin/env python3
"""Eval-lifecycle check for the ExactMatch path.

Validates that the agent authored both halves of the evaluation
harness — an exact-match evaluator config under `evaluations/evaluators/`
AND an evaluation set under `evaluations/eval-sets/` whose `evaluatorRefs`
reference that evaluator — and that `uip codedagent eval --no-report`
actually ran that evaluator over every case of the set and wrote the
results out.

This grades the evaluation HARNESS, not the authored agent: whether the
language tagger gets every case right is the agent's quality, which
depends on the LLM and is not what this task exercises. Scores are
reported as INFO and never fail the check.

Everything is located by CONTENT, never by file count or dictated
filename:

  * The skill's quickstart mandates a `smoke-test.json` eval set for every
    agent, and the prompt asks for a language-tagging eval set — so two
    eval-set files is the *expected* shape, not an error. Any number of
    evaluators / eval sets may exist; the check grades the exact-match
    ones.
  * Results files are matched to eval sets by `evaluationSetName` ==
    the set's `name`, wherever the agent chose to write them.

Checks:
  1. >= 1 evaluator under `evaluations/evaluators/` has
     `evaluatorTypeId == "uipath-exact-match"` and a non-empty `id`.
  2. >= 1 eval set under `evaluations/eval-sets/` has version "1.0",
     `evaluatorRefs` naming an exact-match evaluator, >= 2 test cases,
     and every case's `evaluationCriterias` keyed on that evaluator.
  3. >= 1 qualifying eval set has a results file (top-level
     `evaluationSetResults` list, `evaluationSetName` == set name) with
     one entry per test case, each carrying an `evaluationRunResults`
     entry for the evaluator with a numeric `result.score` — i.e. the
     exact-match evaluator ran on every case. The score VALUE is not
     graded. A qualifying set that was never run is reported but not
     fatal (the graded set is the one the agent ran).
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("lingo-tagger")
EXACT_MATCH_TYPE = "uipath-exact-match"
SKIP_DIRS = {".venv", "node_modules", "__pycache__", ".git"}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def _json_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        sys.exit(f"FAIL: {directory} does not exist")
    files = sorted(p for p in directory.glob("*.json") if p.is_file())
    if not files:
        sys.exit(f"FAIL: {directory} contains no .json files")
    return files


def check_evaluators() -> set[str]:
    """Return the ids of every exact-match evaluator config."""
    ids: set[str] = set()
    seen: list[str] = []
    for path in _json_files(ROOT / "evaluations" / "evaluators"):
        doc = _load_json(path)
        type_id = doc.get("evaluatorTypeId")
        seen.append(f"{path.name} ({type_id!r})")
        if type_id != EXACT_MATCH_TYPE:
            continue
        eval_id = doc.get("id")
        if not eval_id:
            sys.exit(f"FAIL: {path.name} is an exact-match evaluator but is missing `id`")
        ids.add(eval_id)
        print(f'OK: evaluator config {path.name} has evaluatorTypeId={type_id!r} id={eval_id!r}')
    if not ids:
        sys.exit(
            f'FAIL: no evaluator with evaluatorTypeId == "{EXACT_MATCH_TYPE}" under '
            f"evaluations/evaluators/. Found: {', '.join(seen)}"
        )
    return ids


@dataclass
class EvalSet:
    path: Path
    name: str
    evaluator_id: str
    case_count: int


def find_eval_sets(evaluator_ids: set[str]) -> list[EvalSet]:
    """Return every eval set that is wired to an exact-match evaluator."""
    qualifying: list[EvalSet] = []
    rejected: list[str] = []
    for path in _json_files(ROOT / "evaluations" / "eval-sets"):
        doc = _load_json(path)
        if doc.get("version") != "1.0":
            rejected.append(f'{path.name}: version is {doc.get("version")!r}, expected "1.0"')
            continue
        refs = [r for r in (doc.get("evaluatorRefs") or []) if r in evaluator_ids]
        if not refs:
            rejected.append(
                f"{path.name}: evaluatorRefs {doc.get('evaluatorRefs')!r} names no "
                f"exact-match evaluator {sorted(evaluator_ids)}"
            )
            continue
        evaluator_id = refs[0]
        cases = doc.get("evaluations") or []
        if len(cases) < 2:
            rejected.append(f"{path.name}: only {len(cases)} test case(s), need >= 2")
            continue
        unkeyed = [
            case.get("id", f"#{i}")
            for i, case in enumerate(cases)
            if evaluator_id not in (case.get("evaluationCriterias") or {})
        ]
        if unkeyed:
            rejected.append(
                f"{path.name}: test case(s) {unkeyed} do not key evaluationCriterias "
                f"on {evaluator_id!r}"
            )
            continue
        name = doc.get("name") or path.stem
        qualifying.append(EvalSet(path, name, evaluator_id, len(cases)))
        print(
            f'OK: eval set {path.name} ("{name}") references {evaluator_id!r} '
            f"across {len(cases)} test cases"
        )
    if not qualifying:
        sys.exit(
            "FAIL: no eval set under evaluations/eval-sets/ is wired to an "
            "exact-match evaluator. " + " | ".join(rejected)
        )
    return qualifying


def _find_results_files() -> dict[str, list[Path]]:
    """Map `evaluationSetName` -> results files carrying that name.

    `uip codedagent eval --output-file <name>` lets the caller pick the
    filename and location, so results are found by the documented
    top-level shape and matched to their eval set by name.
    """
    found: dict[str, list[Path]] = {}
    for p in sorted(ROOT.rglob("*.json")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(doc, dict) and isinstance(doc.get("evaluationSetResults"), list):
            found.setdefault(str(doc.get("evaluationSetName")), []).append(p)
    return found


def _validate_results(path: Path, eval_set: EvalSet) -> list[str]:
    """Return a list of problems with one results file for one eval set."""
    doc = _load_json(path)
    cases = doc.get("evaluationSetResults")
    if not isinstance(cases, list) or not cases:
        return [f"{path.name}: `evaluationSetResults` is missing or empty"]
    problems: list[str] = []
    if len(cases) != eval_set.case_count:
        problems.append(
            f"{path.name}: {len(cases)} entries in evaluationSetResults, but eval set "
            f"{eval_set.path.name} has {eval_set.case_count} test cases"
        )
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_name = case.get("evaluationName") or "?"
        matching = [
            r for r in (case.get("evaluationRunResults") or [])
            if isinstance(r, dict) and r.get("evaluatorId") == eval_set.evaluator_id
        ]
        if not matching:
            problems.append(
                f"{path.name} {case_name!r}: no evaluationRunResults entry for "
                f"evaluatorId={eval_set.evaluator_id!r}"
            )
            continue
        for r in matching:
            score = (r.get("result") or {}).get("score")
            if not isinstance(score, (int, float)):
                problems.append(
                    f"{path.name} {case_name!r}: evaluator {eval_set.evaluator_id!r} "
                    f"run has no numeric `result.score` (got {score!r}) — the "
                    f"evaluator did not actually run"
                )
    return problems


def _score_summary(path: Path, eval_set: EvalSet) -> str:
    """Informational: how the authored agent fared. Not graded."""
    doc = _load_json(path)
    scores = [
        (r.get("result") or {}).get("score")
        for case in doc.get("evaluationSetResults") or []
        if isinstance(case, dict)
        for r in case.get("evaluationRunResults") or []
        if isinstance(r, dict) and r.get("evaluatorId") == eval_set.evaluator_id
    ]
    nums = [s for s in scores if isinstance(s, (int, float))]
    if not nums:
        return "no scores"
    perfect = sum(1 for s in nums if s == 1.0)
    return f"{perfect}/{len(nums)} cases scored 1.0 (avg {sum(nums) / len(nums):.2f})"


def check_results(eval_sets: list[EvalSet]) -> None:
    by_name = _find_results_files()
    if not by_name:
        sys.exit(
            "FAIL: no eval-results JSON with a top-level `evaluationSetResults` "
            "list found in the project — `uip codedagent eval --output-file` "
            "likely never produced results"
        )
    validated = 0
    unrun: list[str] = []
    problems: list[str] = []
    for es in eval_sets:
        paths = by_name.get(es.name)
        if not paths and len(eval_sets) == 1 and len(by_name) == 1:
            # Single set, single results file: pair them even if the name drifted.
            paths = next(iter(by_name.values()))
        if not paths:
            unrun.append(f'{es.path.name} ("{es.name}")')
            continue
        for p in paths:
            bad = _validate_results(p, es)
            if bad:
                problems.extend(bad)
            else:
                validated += 1
                print(
                    f"OK: {p.relative_to(ROOT)} covers eval set {es.path.name}: "
                    f"{es.evaluator_id!r} ran on all {es.case_count} case(s)"
                )
                print(f"INFO: {p.relative_to(ROOT)}: {_score_summary(p, es)} (not graded)")
    if problems:
        sys.exit("FAIL: " + " | ".join(problems))
    if validated == 0:
        sys.exit(
            "FAIL: results files exist "
            f"({', '.join(str(p.relative_to(ROOT)) for ps in by_name.values() for p in ps)}) "
            f"but none has evaluationSetName matching a qualifying eval set "
            f"({', '.join(unrun)})"
        )
    if unrun:
        print(f"NOTE: eval set(s) authored but not run: {', '.join(unrun)}")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    evaluator_ids = check_evaluators()
    eval_sets = find_eval_sets(evaluator_ids)
    check_results(eval_sets)


if __name__ == "__main__":
    main()
