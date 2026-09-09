#!/usr/bin/env python3
"""Behavioural check: every row of every eval set in the project passes when the
workflow is run with the row's inputs and scored by the project's evaluator, exactly
as Studio Web's Evaluations panel would score it (strict deep-equal on the RAW output).

Usage: check_rows_pass.py <project-dir> [--min-rows N]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from eval_scoring import print_results, score_project  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("project")
parser.add_argument("--min-rows", type=int, default=1)
args = parser.parse_args()

if not Path(args.project, "Workflow.json").is_file():
    sys.exit(f"FAIL: {args.project}/Workflow.json not found")

results = score_project(args.project)
print_results(results)
if len(results) < args.min_rows:
    sys.exit(f"FAIL: {len(results)} scored row(s), expected at least {args.min_rows}")
failing = [r for r in results if r["verdict"] != "pass"]
if failing:
    sys.exit(f"FAIL: {len(failing)}/{len(results)} row(s) do not pass under uipath-exact-match")
print(f"OK: {len(results)}/{len(results)} rows pass")
