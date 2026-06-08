#!/usr/bin/env python3
"""Eval-lifecycle check: both documented mocking patterns + JsonSimilarity.

The agent must pin BOTH mocking patterns (the skill documents two of
them, and a real agent will reach for one or the other depending on
the call shape):

  - Declarative `mockingStrategy: mockito` on at least one test case,
    mocking the UiPath SDK asset retrieval helper.
  - In-code `@mockable(example_calls=[...])` on at least one function
    in `main.py`, paired with the `ExampleCall` import from
    `uipath.eval.mocks`. This is what makes the `requests.get`-style
    helper substitutable at eval time without a real network call.

Output evaluator: `JsonSimilarityEvaluator`
(`evaluatorTypeId == "uipath-json-similarity"`). The agent's output
is structured JSON, so JsonSimilarity is the natural fit and it
exercises a separate evaluator type from `eval_exact_match`.

Checks:
  1. `asset-retriever/pyproject.toml` exists with no `[build-system]`.
  2. `asset-retriever/main.py` imports `mockable` and `ExampleCall` from
     `uipath.eval.mocks` AND has at least one `@mockable(...)`
     decorator.
  3. `asset-retriever/evaluations/evaluators/*.json` contains an
     evaluator with `evaluatorTypeId == "uipath-json-similarity"`.
  4. `asset-retriever/evaluations/eval-sets/*.json` is v1.0; at least
     one test case carries `mockingStrategy.type == "mockito"` with
     a non-empty return behavior.
  5. `asset-retriever/eval-results.json` has the documented shape and
     every recorded evaluator run scored >= 0.5.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("asset-retriever")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_single_json(directory: Path) -> Path:
    if not directory.is_dir():
        sys.exit(f"FAIL: {directory} does not exist")
    files = sorted(p for p in directory.glob("*.json") if p.is_file())
    if not files:
        sys.exit(f"FAIL: {directory} contains no .json files")
    return files[0]


def check_pyproject() -> None:
    text = _read_text(ROOT / "pyproject.toml")
    if "[build-system]" in text:
        sys.exit(
            "FAIL: pyproject.toml contains a [build-system] section — "
            "Critical Rule C1 forbids it."
        )
    print("OK: pyproject.toml has no [build-system]")


def check_in_code_mocking() -> None:
    """Pattern 2: in-code `@mockable` paired with `ExampleCall`."""
    main = _read_text(ROOT / "main.py")
    if "from uipath.eval.mocks" not in main:
        sys.exit(
            "FAIL: main.py does not import from `uipath.eval.mocks`. The "
            "`@mockable`/`ExampleCall` pair is documented as the in-code "
            "mocking pattern; one of the two external calls should use it."
        )
    if "mockable" not in main:
        sys.exit(
            "FAIL: main.py imports from `uipath.eval.mocks` but never uses "
            "`mockable`. The decorator must wrap at least one helper."
        )
    if "ExampleCall" not in main:
        sys.exit(
            "FAIL: main.py does not reference `ExampleCall`. `@mockable` "
            "needs `example_calls=[ExampleCall(...)]` to supply mock outputs."
        )
    if "@mockable" not in main:
        sys.exit(
            "FAIL: main.py imports `mockable` but no function is decorated "
            "with `@mockable(...)`. The decoration is what makes the "
            "function substitutable at eval time."
        )
    print("OK: main.py wires the in-code @mockable pattern with ExampleCall")


def check_json_similarity_evaluator() -> str:
    """Pattern 1 of two: structured-output evaluator."""
    evals_dir = ROOT / "evaluations" / "evaluators"
    if not evals_dir.is_dir():
        sys.exit(f"FAIL: {evals_dir} does not exist")
    matched_ids: list[str] = []
    for path in sorted(evals_dir.glob("*.json")):
        doc = _load_json(path)
        if doc.get("evaluatorTypeId") == "uipath-json-similarity":
            matched_ids.append(doc.get("id") or path.stem)
    if not matched_ids:
        sys.exit(
            "FAIL: no evaluator with `evaluatorTypeId == \"uipath-json-"
            "similarity\"` found. The agent emits structured JSON output; "
            "JsonSimilarityEvaluator is the documented fit for this shape."
        )
    print(f"OK: JsonSimilarityEvaluator wired (ids: {matched_ids})")
    return matched_ids[0]


def _has_mockito_with_return(case: dict) -> bool:
    strategy = case.get("mockingStrategy") or {}
    if strategy.get("type") != "mockito":
        return False
    for b in strategy.get("behaviors") or []:
        if not isinstance(b, dict):
            continue
        for step in b.get("then") or []:
            if isinstance(step, dict) and step.get("type") == "return" and step.get("value") is not None:
                return True
    return False


def check_eval_set() -> int:
    """Pattern 1 of mocking: declarative mockito for the asset call."""
    path = find_single_json(ROOT / "evaluations" / "eval-sets")
    doc = _load_json(path)
    if doc.get("version") != "1.0":
        sys.exit(
            f'FAIL: {path.name} version should be "1.0", '
            f'got {doc.get("version")!r}'
        )
    cases = doc.get("evaluations") or []
    if not cases:
        sys.exit(f"FAIL: {path.name} has no test cases in `evaluations`")
    cases_with_mocks = [c for c in cases if _has_mockito_with_return(c)]
    if not cases_with_mocks:
        sys.exit(
            f'FAIL: no test case in {path.name} carries a '
            f'`mockingStrategy.type == "mockito"` with a non-empty return. '
            f'The asset retrieval must be mocked declaratively for offline '
            f'evals to pass.'
        )
    print(
        f"OK: {path.name} carries declarative mockito mocks on "
        f"{len(cases_with_mocks)}/{len(cases)} test case(s)"
    )
    return len(cases)


def check_results(expected_case_count: int) -> None:
    path = ROOT / "eval-results.json"
    doc = _load_json(path)
    if not isinstance(doc, dict):
        sys.exit(
            f"FAIL: {path.name} top-level should be an object, "
            f"got {type(doc).__name__}"
        )
    cases = doc.get("evaluationSetResults")
    if not isinstance(cases, list) or not cases:
        sys.exit(
            f"FAIL: {path.name} is missing a non-empty "
            f"`evaluationSetResults` list. Top-level keys: {list(doc.keys())}"
        )
    if len(cases) != expected_case_count:
        sys.exit(
            f"FAIL: expected {expected_case_count} entries in "
            f"`evaluationSetResults` (one per eval-set test case), "
            f"got {len(cases)}"
        )
    bad = []
    total_runs = 0
    for case in cases:
        if not isinstance(case, dict):
            continue
        name = case.get("evaluationName") or "?"
        runs = case.get("evaluationRunResults") or []
        if not runs:
            bad.append(f"{name!r}: no evaluationRunResults entries")
            continue
        for r in runs:
            if not isinstance(r, dict):
                continue
            total_runs += 1
            score = (r.get("result") or {}).get("score")
            if not isinstance(score, (int, float)) or score < 0.5:
                bad.append(
                    f"{name!r}: evaluator {r.get('evaluatorId')!r} scored "
                    f"{score!r} (expected >= 0.5 — both mocks should make "
                    f"the agent run deterministically)"
                )
    if bad:
        sys.exit("FAIL: " + " | ".join(bad))
    print(
        f"OK: every eval case has at least one evaluator run scoring "
        f">= 0.5 ({total_runs} run(s) across {len(cases)} case(s))"
    )


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_in_code_mocking()
    check_json_similarity_evaluator()
    case_count = check_eval_set()
    check_results(case_count)


if __name__ == "__main__":
    main()
