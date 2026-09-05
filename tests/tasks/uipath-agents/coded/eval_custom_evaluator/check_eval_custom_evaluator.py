#!/usr/bin/env python3
"""Custom evaluator lifecycle check.

Verifies the agent scaffolded a custom evaluator via the CLI, registered
it to produce a JSON spec, wired it into an eval set, and ran it.

Checks:
  1. `evaluations/evaluators/custom/<file>.py` exists.
  2. `evaluations/evaluators/<file>.json` exists with
     `evaluatorSchema`, `evaluatorTypeId`, and a non-empty `id`.
  3. The evaluator schema and evaluator type file references resolve
     relative to the evaluator JSON spec.
  4. The eval set under `evaluations/eval-sets/` whose `evaluatorRefs`
     references the custom evaluator id has version "1.0", at least
     2 test cases, and each test case's `evaluationCriterias` keys
     the evaluator id.
  5. A results JSON (any name) whose `evaluationSetResults` include
     runs for the custom evaluator id matches the expected case count;
     every case has a numeric score from the custom evaluator and at
     least one case scores > 0 (deliberate negative-control cases that
     score 0 are allowed).
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

ROOT = find_project_root("topic-detector")


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _resolve_file_ref(spec_path: Path, value: str, field_name: str) -> Path:
    if not value.startswith("file://"):
        sys.exit(f"FAIL: evaluator JSON spec missing `{field_name}` with `file://` reference. Got: {value!r}")
    ref = value.removeprefix("file://")
    # Class-qualified refs use file://path/to/file.py:ClassName.
    ref_path = ref.split(":", 1)[0]
    if not ref_path:
        sys.exit(f"FAIL: evaluator JSON spec `{field_name}` has an empty file path. Got: {value!r}")
    candidates = [
        (spec_path.parent / ref_path).resolve(),
        (spec_path.parent / "custom" / ref_path).resolve(),
    ]
    path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    if not path.is_file():
        sys.exit(
            f"FAIL: evaluator JSON spec `{field_name}` points at {value!r}, "
            "but none of these candidate paths exist: "
            f"{', '.join(str(candidate) for candidate in candidates)}"
        )
    return path


def check_custom_evaluator_py() -> str:
    custom_dir = ROOT / "evaluations" / "evaluators" / "custom"
    if not custom_dir.is_dir():
        sys.exit(f"FAIL: {custom_dir} does not exist — `uip codedagent add evaluator` not run")
    py_files = sorted(custom_dir.glob("*.py"))
    if not py_files:
        sys.exit(f"FAIL: no Python file in {custom_dir}")
    print(f"OK: custom evaluator Python file exists: {py_files[0].name}")
    return py_files[0].stem


def check_custom_evaluator_json() -> tuple[str, Path]:
    # register writes the spec to evaluations/evaluators/, not evaluations/evaluators/custom/
    evaluators_dir = ROOT / "evaluations" / "evaluators"
    json_files = sorted(f for f in evaluators_dir.glob("*.json") if "evaluatorSchema" in f.read_text() and "file://" in f.read_text())
    if not json_files:
        sys.exit(f"FAIL: no JSON spec with evaluatorSchema in {evaluators_dir} — `uip codedagent register evaluator` not run")
    spec_path = json_files[0]
    spec = _load_json(spec_path)
    schema_path = _resolve_file_ref(spec_path, spec.get("evaluatorSchema") or "", "evaluatorSchema")
    eval_id = spec.get("id")
    if not eval_id:
        sys.exit("FAIL: evaluator JSON spec missing required `id` field")
    type_path = _resolve_file_ref(spec_path, spec.get("evaluatorTypeId") or "", "evaluatorTypeId")
    if type_path.parent.name != "types":
        sys.exit(
            "FAIL: evaluator JSON spec `evaluatorTypeId` should point into a "
            f"`types/` directory. Got: {_relative(type_path)}"
        )
    print(
        "OK: evaluator JSON spec exists with "
        f"id={eval_id!r}, evaluatorSchema={_relative(schema_path)!r}, "
        f"evaluatorTypeId={_relative(type_path)!r}"
    )
    return eval_id, type_path


def check_custom_evaluator_types(type_path: Path) -> None:
    if not type_path.is_file():
        sys.exit(f"FAIL: evaluator type file {type_path} does not exist")
    print(f"OK: evaluator types file exists: {_relative(type_path)}")


def check_eval_set(evaluator_id: str) -> int:
    eval_sets_dir = ROOT / "evaluations" / "eval-sets"
    if not eval_sets_dir.is_dir():
        sys.exit(f"FAIL: {eval_sets_dir} does not exist")
    json_files = sorted(eval_sets_dir.glob("*.json"))
    if not json_files:
        sys.exit(f"FAIL: no eval set JSON in {eval_sets_dir}")
    # Grade the eval set that references the custom evaluator; others may exist.
    docs = {p: _load_json(p) for p in json_files}
    matching = [p for p, d in docs.items() if evaluator_id in (d.get("evaluatorRefs") or [])]
    if not matching:
        refs = {p.name: (d.get("evaluatorRefs") or []) for p, d in docs.items()}
        sys.exit(f"FAIL: no eval set `evaluatorRefs` includes {evaluator_id!r}. Got: {refs}")
    set_path = matching[0]
    doc = docs[set_path]
    if doc.get("version") != "1.0":
        sys.exit(f'FAIL: eval set {set_path.name} version should be "1.0", got {doc.get("version")!r}')
    cases = doc.get("evaluations") or []
    if len(cases) < 2:
        sys.exit(f"FAIL: eval set {set_path.name} must have at least 2 test cases, got {len(cases)}")
    for i, case in enumerate(cases):
        crit = case.get("evaluationCriterias") or {}
        if evaluator_id not in crit:
            sys.exit(
                f"FAIL: {set_path.name} test case {i} (`{case.get('id', '?')}`) does not key "
                f"evaluationCriterias on {evaluator_id!r}. Got keys: {list(crit.keys())}"
            )
    print(f"OK: eval set {set_path.name} references {evaluator_id!r} across {len(cases)} test cases")
    return len(cases)


def _find_results_file(evaluator_id: str) -> Path:
    """Locate the eval-results JSON by content, not a dictated filename.

    `uip codedagent eval --output-file <name>` lets the caller pick the
    name; accept any JSON in the project or cwd carrying the documented
    `evaluationSetResults` shape whose run results include the custom
    evaluator id.
    """
    skip = {".venv", "node_modules", "__pycache__", ".git"}
    roots = [ROOT, Path(os.getcwd())]
    seen: set[Path] = set()
    shaped: list[Path] = []
    for base in roots:
        for p in sorted(base.rglob("*.json")):
            if p in seen or any(part in skip for part in p.parts):
                continue
            seen.add(p)
            try:
                doc = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            cases = doc.get("evaluationSetResults") if isinstance(doc, dict) else None
            if not isinstance(cases, list):
                continue
            shaped.append(p)
            for case in cases:
                runs = (case or {}).get("evaluationRunResults") or []
                if any(isinstance(r, dict) and r.get("evaluatorId") == evaluator_id for r in runs):
                    return p
    if shaped:
        sys.exit(
            f"FAIL: found eval-results JSON ({', '.join(_relative(p) for p in shaped)}) "
            f"but none contain runs for {evaluator_id!r} — the custom evaluator's eval set was not run"
        )
    sys.exit(
        "FAIL: no eval-results JSON with a top-level `evaluationSetResults` "
        "list found — `uip codedagent eval --output-file` likely never "
        "produced results"
    )


def check_results(evaluator_id: str, expected_case_count: int) -> None:
    path = _find_results_file(evaluator_id)
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
    positive = 0
    for case in cases:
        runs = case.get("evaluationRunResults") or []
        matching = [r for r in runs if isinstance(r, dict) and r.get("evaluatorId") == evaluator_id]
        if not matching:
            bad_missing.append(case.get("evaluationName") or "?")
            continue
        scores = [(r.get("result") or {}).get("score") for r in matching]
        if not all(isinstance(sc, (int, float)) for sc in scores):
            bad_score.append(case.get("evaluationName") or "?")
        elif any(sc > 0 for sc in scores):
            positive += 1
    if bad_missing:
        sys.exit(f"FAIL: no evaluationRunResults for {evaluator_id!r} in cases: {bad_missing}")
    if bad_score:
        sys.exit(f"FAIL: custom evaluator produced no numeric score in cases: {bad_score}")
    # Negative-control cases (deliberately wrong expectation) legitimately score 0;
    # require a positive signal on at least one case.
    if positive < 1:
        sys.exit(
            f"FAIL: custom evaluator scored 0 on all {len(cases)} case(s) — "
            "it ran but never recognised a correct answer"
        )
    print(
        f"OK: eval-results has {len(cases)} result(s) with custom evaluator runs; "
        f"{positive} scored > 0 ({len(cases) - positive} zero-score / negative-control case(s))"
    )


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_custom_evaluator_py()
    evaluator_id, type_path = check_custom_evaluator_json()
    check_custom_evaluator_types(type_path)
    case_count = check_eval_set(evaluator_id)
    check_results(evaluator_id, case_count)


if __name__ == "__main__":
    main()
