#!/usr/bin/env python3
"""Verify the deterministic eval-run e2e produced a clean 1.0 across all 3 data points.

Reads `eval-results.json` (the JSON the agent saved from
`uip maestro flow eval run results <run_id> --verbose --output json`) and
asserts:

  1. Top-level `Code` is `MaestroFlowEvalRunResults`.
  2. There are at least 3 per-data-point rows.
  3. Every row has `Status == "Completed"`.
  4. No row has a non-empty `Error`.
  5. For each row, every entry in `EvaluatorScores` (or its singular
     equivalent) reports a score of 1.0 — the agent + evaluator were both
     deterministic, so anything else is a regression.

The CLI's exact field names may evolve; we tolerate both `EvaluatorScores`
(list/dict of evaluator entries) and a flat per-row `Score` field. Anything
that surfaces a numeric score gets checked.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS_PATH = Path("eval-results.json")
EXPECTED_DATA_POINTS = 3


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _load() -> dict:
    if not RESULTS_PATH.is_file():
        _fail(f"Missing {RESULTS_PATH}")
    try:
        return json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fail(f"{RESULTS_PATH} is not valid JSON: {e}")


def _extract_rows(doc: dict) -> list[dict]:
    """The CLI envelope is `{ Code, Data: { Results: [...] } }`. Tolerate
    minor key-name drift by walking common containers.
    """
    code = doc.get("Code")
    if code != "MaestroFlowEvalRunResults":
        _fail(
            f'eval-results.json `Code` should be "MaestroFlowEvalRunResults", '
            f'got {code!r}'
        )
    data = doc.get("Data") or {}
    for key in ("Results", "DataPoints", "Rows"):
        rows = data.get(key)
        if isinstance(rows, list) and rows:
            return rows
    _fail(
        f'eval-results.json has no Results/DataPoints/Rows list under Data. '
        f'Top-level keys: {list(doc.keys())}, Data keys: {list(data.keys())}'
    )
    return []  # unreachable


def _row_scores(row: dict) -> list[float]:
    """Pull every numeric score this row reports, regardless of shape."""
    scores: list[float] = []
    flat = row.get("Score")
    if isinstance(flat, (int, float)):
        scores.append(float(flat))
    es = row.get("EvaluatorScores")
    if isinstance(es, list):
        for e in es:
            if isinstance(e, dict):
                v = e.get("Score")
                if v is None:
                    v = e.get("score")
                if isinstance(v, (int, float)):
                    scores.append(float(v))
    elif isinstance(es, dict):
        for v in es.values():
            if isinstance(v, (int, float)):
                scores.append(float(v))
            elif isinstance(v, dict):
                inner = v.get("Score")
                if inner is None:
                    inner = v.get("score")
                if isinstance(inner, (int, float)):
                    scores.append(float(inner))
    return scores


def main() -> None:
    doc = _load()
    rows = _extract_rows(doc)
    if len(rows) < EXPECTED_DATA_POINTS:
        _fail(
            f"expected at least {EXPECTED_DATA_POINTS} data-point rows, got {len(rows)}"
        )
    print(f"OK: eval-results.json has {len(rows)} data-point rows")

    failures: list[str] = []
    for row in rows:
        name = row.get("DataPoint") or row.get("Name") or "?"
        status = row.get("Status")
        err = row.get("Error")
        if str(status).lower() != "completed":
            failures.append(f"{name!r}: Status={status!r} (expected Completed)")
            continue
        if err:
            failures.append(f"{name!r}: Error={err!r}")
            continue
        scores = _row_scores(row)
        if not scores:
            failures.append(
                f"{name!r}: no numeric score found (row keys: {list(row.keys())})"
            )
            continue
        bad = [s for s in scores if s != 1.0]
        if bad:
            failures.append(
                f"{name!r}: scored {bad!r} (expected 1.0 from exact-match)"
            )

    if failures:
        _fail(" | ".join(failures))
    print(
        f"OK: every data point Completed with score 1.0 across "
        f"{sum(len(_row_scores(r)) for r in rows)} evaluator run(s)"
    )


if __name__ == "__main__":
    main()
