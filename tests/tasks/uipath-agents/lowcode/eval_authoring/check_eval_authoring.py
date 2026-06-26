#!/usr/bin/env python3
"""Low-code eval authoring check (offline path).

Validates that the agent built an evaluation harness on the low-code
`FaqAgent` using the documented `evals/` layout:

  1. A deterministic evaluator exists under `evals/evaluators/` — a
     legacy Exact Match (`type` 1, `category` 0) or JSON Similarity
     (`type` 6, `category` 0) evaluator with a non-empty `id`. The two
     `uip agent init` defaults are both LLM-as-a-judge (category 1) /
     trajectory (category 3), so a category-0 evaluator proves the agent
     authored a new one beyond the scaffolded defaults.
  2. That deterministic evaluator's `id` is listed in some eval set's
     `evaluatorRefs` (it is actually wired in, not orphaned).
  3. The Default Evaluation Set has >=2 inline test cases in
     `evaluations[]` (added via `uip agent eval add`).

Casing/field names follow references/lowcode/evaluations/evaluators.md
and evaluation-sets.md.
"""

import json
import os
import sys
from pathlib import Path

AGENT_DIR = Path(os.getcwd()) / "EvalSol" / "FaqAgent"
EVALUATORS_DIR = AGENT_DIR / "evals" / "evaluators"
EVAL_SETS_DIR = AGENT_DIR / "evals" / "eval-sets"

# Deterministic (category 0) legacy evaluator types: Exact Match = 1, JSON Similarity = 6.
DETERMINISTIC_TYPES = {1, 6}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def load_all(directory: Path) -> list[tuple[Path, dict]]:
    if not directory.is_dir():
        sys.exit(f"FAIL: {directory} does not exist")
    out: list[tuple[Path, dict]] = []
    for p in sorted(directory.glob("*.json")):
        try:
            out.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, json.JSONDecodeError):
            continue
    if not out:
        sys.exit(f"FAIL: {directory} contains no readable .json files")
    return out


def find_deterministic_evaluator(evaluators: list[tuple[Path, dict]]) -> str:
    for path, doc in evaluators:
        try:
            etype = int(doc.get("type"))
            category = int(doc.get("category"))
        except (TypeError, ValueError):
            continue
        if etype in DETERMINISTIC_TYPES and category == 0:
            eval_id = doc.get("id")
            if not eval_id:
                sys.exit(f"FAIL: deterministic evaluator {path.name} is missing an `id`")
            print(
                f"OK: deterministic evaluator {path.name} "
                f"(type={etype}, category=0, id={eval_id})"
            )
            return eval_id
    types_seen = [(d.get("type"), d.get("category")) for _, d in evaluators]
    sys.exit(
        "FAIL: no deterministic (category 0) Exact Match (type 1) or JSON "
        "Similarity (type 6) evaluator found under evals/evaluators/. The "
        "uip agent init defaults are LLM-based only, so a new one must be "
        f"authored. (type, category) seen: {types_seen}"
    )


def assert_referenced_and_cases(eval_id: str) -> None:
    eval_sets = load_all(EVAL_SETS_DIR)

    referenced = False
    for _, doc in eval_sets:
        if eval_id in (doc.get("evaluatorRefs") or []):
            referenced = True
            break
    if not referenced:
        sys.exit(
            f"FAIL: deterministic evaluator id {eval_id!r} is not listed in any "
            "eval set's evaluatorRefs — it was authored but never wired in."
        )
    print(f"OK: evaluator {eval_id} is referenced in an eval set's evaluatorRefs")

    default = None
    for _, doc in eval_sets:
        if doc.get("name") == "Default Evaluation Set":
            default = doc
            break
    if default is None:
        # Fall back to any eval set that references the deterministic evaluator.
        for _, doc in eval_sets:
            if eval_id in (doc.get("evaluatorRefs") or []):
                default = doc
                break
    if default is None:
        sys.exit("FAIL: could not locate the Default Evaluation Set")

    cases = default.get("evaluations")
    if not isinstance(cases, list):
        sys.exit(f"FAIL: eval set `evaluations` must be a list, got {cases!r}")
    non_empty = [c for c in cases if isinstance(c, dict) and c]
    if len(non_empty) < 2:
        sys.exit(
            f"FAIL: eval set {default.get('name')!r} must have >=2 inline test "
            f"cases in `evaluations[]` (added with `uip agent eval add`), "
            f"got {len(non_empty)}"
        )
    print(
        f"OK: eval set {default.get('name')!r} has {len(non_empty)} inline test cases"
    )


def main() -> None:
    if not AGENT_DIR.is_dir():
        sys.exit(f"FAIL: agent directory {AGENT_DIR} does not exist")
    evaluators = load_all(EVALUATORS_DIR)
    eval_id = find_deterministic_evaluator(evaluators)
    assert_referenced_and_cases(eval_id)


if __name__ == "__main__":
    main()
