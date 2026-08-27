#!/usr/bin/env python3
"""Structural check of the project's `evals/` files against the Unified Eval layout
Studio Web's Evaluations panel reads — the things that silently break the panel:

- files live at evals/<scope>/eval-sets/*.json and evals/<scope>/evaluators/*.json
- `evaluatorRefs` and `evaluationCriterias` keys are evaluator FILE base names
- every evaluator is `uipath-exact-match` with an `evaluatorConfig`
- every row has an `id`, an `inputs` object and its expectedOutput INSIDE
  `evaluationCriterias["<ref>"]`, not at the row top level

Usage: check_eval_contract.py <project-dir> [--min-rows N]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_scoring import load_eval_sets, load_evaluators  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("project")
parser.add_argument("--min-rows", type=int, default=1)
args = parser.parse_args()

problems = []
set_paths = load_eval_sets(args.project)
if not set_paths:
    sys.exit(f"FAIL: no eval set at {args.project}/evals/<scope>/eval-sets/*.json")
evaluators = load_evaluators(args.project)
if not evaluators:
    sys.exit(f"FAIL: no evaluator at {args.project}/evals/<scope>/evaluators/*.json")

for ref, evaluator in evaluators.items():
    if evaluator.get("evaluatorTypeId") != "uipath-exact-match":
        problems.append(f"evaluator {ref}: evaluatorTypeId is {evaluator.get('evaluatorTypeId')!r}, expected 'uipath-exact-match'")
    if not isinstance(evaluator.get("evaluatorConfig"), dict):
        problems.append(f"evaluator {ref}: missing evaluatorConfig object")
    for key in ("id", "version"):
        if not evaluator.get(key):
            problems.append(f"evaluator {ref}: missing {key!r}")

total_rows = 0
for set_path in set_paths:
    eval_set = json.loads(set_path.read_text())
    label = set_path.name
    for key in ("id", "name", "version"):
        if not eval_set.get(key):
            problems.append(f"{label}: missing {key!r}")
    refs = eval_set.get("evaluatorRefs")
    if not isinstance(refs, list) or not refs:
        problems.append(f"{label}: evaluatorRefs must be a non-empty list")
        refs = []
    for ref in refs:
        if ref.endswith(".json"):
            problems.append(f"{label}: evaluatorRefs entry {ref!r} must be the file base name without .json")
        elif ref not in evaluators:
            problems.append(f"{label}: evaluatorRefs entry {ref!r} has no evals/<scope>/evaluators/{ref}.json")
    rows = eval_set.get("evaluations")
    if not isinstance(rows, list):
        problems.append(f"{label}: evaluations must be a list")
        continue
    total_rows += len(rows)
    for row in rows:
        name = row.get("name") or row.get("id") or "<unnamed>"
        if not row.get("id"):
            problems.append(f"{label}/{name}: row has no id")
        if not isinstance(row.get("inputs"), dict):
            problems.append(f"{label}/{name}: inputs must be an object")
        criterias = row.get("evaluationCriterias")
        if not isinstance(criterias, dict) or not criterias:
            problems.append(f"{label}/{name}: evaluationCriterias missing — expectedOutput belongs under it, keyed by evaluator ref")
            continue
        for key, criteria in criterias.items():
            if key not in refs and key.removesuffix(".json") not in refs:
                problems.append(f"{label}/{name}: evaluationCriterias key {key!r} is not in evaluatorRefs")
            if not isinstance(criteria, dict) or "expectedOutput" not in criteria:
                problems.append(f"{label}/{name}: evaluationCriterias[{key!r}] has no expectedOutput")

if total_rows < args.min_rows:
    problems.append(f"{total_rows} row(s) in total, expected at least {args.min_rows}")

if problems:
    print("\n".join(f"- {p}" for p in problems))
    sys.exit(f"FAIL: {len(problems)} contract problem(s)")
print(f"OK: {len(set_paths)} eval set(s), {len(evaluators)} evaluator(s), {total_rows} row(s) match the Unified Eval contract")
