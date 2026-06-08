#!/usr/bin/env python3
"""Validate a targeted `uip codedagent eval --eval-ids` run."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("subset-eval")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")
    if not isinstance(value, dict):
        fail(f"{path} should contain a JSON object")
    return value


def walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def result_case_ids(case: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("evaluationId", "id", "testId", "caseId"):
        value = case.get(key)
        if value:
            ids.add(str(value))
    return ids


def result_case_label(case: dict[str, Any]) -> str:
    for key in (
        "evaluationId",
        "evaluationName",
        "id",
        "testId",
        "testName",
        "caseId",
        "name",
    ):
        value = case.get(key)
        if value:
            return str(value)
    return json.dumps(case, sort_keys=True)


def rowish(row: dict[str, Any]) -> bool:
    id_keys = {"evaluationId", "evaluationName", "id", "testId", "testName", "caseId", "name"}
    result_keys = {"evaluationRunResults", "evaluationResults", "result", "score", "Score"}
    return bool(id_keys & set(row)) and bool(result_keys & set(row))


def extract_result_rows(results: dict[str, Any]) -> list[dict[str, Any]]:
    if rowish(results):
        return [results]

    for key in (
        "evaluationSetResults",
        "testResults",
        "results",
        "Results",
        "rows",
        "Rows",
    ):
        rows = results.get(key)
        if isinstance(rows, list) and all(isinstance(row, dict) for row in rows):
            selected = [row for row in rows if rowish(row)]
            if selected:
                return selected

    data = results.get("Data")
    if isinstance(data, dict):
        rows = extract_result_rows(data)
        if rows:
            return rows
    elif isinstance(data, list) and all(isinstance(row, dict) for row in data):
        selected = [row for row in data if rowish(row)]
        if selected:
            return selected

    for item in walk(results):
        if (
            isinstance(item, list)
            and item
            and all(isinstance(row, dict) for row in item)
            and any(rowish(row) for row in item)
        ):
            return [row for row in item if rowish(row)]
    return []


def result_scores(row: dict[str, Any]) -> list[float]:
    scores: list[float] = []
    for item in walk(row):
        if not isinstance(item, dict):
            continue
        for key in ("score", "Score"):
            value = item.get(key)
            if isinstance(value, (int, float)):
                scores.append(float(value))
            elif isinstance(value, str):
                try:
                    scores.append(float(value))
                except ValueError:
                    pass
    return scores


def main() -> None:
    if not ROOT.is_dir():
        fail(f"project directory {ROOT} does not exist")

    eval_sets = sorted((ROOT / "evaluations" / "eval-sets").glob("*.json"))
    if not eval_sets:
        fail("no eval-set JSON found")
    eval_set = load(eval_sets[0])
    cases = eval_set.get("evaluations") or []
    ids = {c.get("id") for c in cases if isinstance(c, dict)}
    expected_ids = {"case-selected", "case-skipped-a", "case-skipped-b"}
    if ids != expected_ids:
        fail(f"eval-set case ids should be {sorted(expected_ids)}, got {sorted(ids)}")

    result_path = ROOT / "selected-results.json"
    if not result_path.is_file():
        result_path = Path("selected-results.json")
    if not result_path.is_file():
        fail("selected-results.json was not written")
    results = load(result_path)
    rows = extract_result_rows(results)
    if not rows:
        fail(f"selected-results.json has no recognizable result rows. Keys: {list(results)}")
    names = [result_case_label(row) for row in rows]
    if len(rows) != 1:
        fail(f"expected exactly one selected result row, got {len(rows)} rows: {names}")
    if "case-selected" not in result_case_ids(rows[0]):
        fail(f"the only result row should have id case-selected, got {names[0]!r}")

    scores = result_scores(rows[0])
    if not scores:
        fail("selected result row has no score values")
    bad_scores = [score for score in scores if score != 1.0]
    if bad_scores:
        fail(f"selected case should score 1.0, got bad scores {bad_scores!r}")
    print("OK: eval set has three cases, --eval-ids run saved only case-selected with score 1.0")


if __name__ == "__main__":
    main()
