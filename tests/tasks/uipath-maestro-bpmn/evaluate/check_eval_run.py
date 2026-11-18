#!/usr/bin/env python3
"""Grade the live BPMN eval-run tasks (`eval_run/`, `eval_run_compare/`).

Both tasks build the same tiny deterministic process (no inputs; a script task
returns 6 * 7 as the `product` output), score it with an exact-match evaluator,
and run the eval set against the connected tenant. They differ in which
`uip maestro bpmn eval run` verbs they exercise:

  eval_run          start (once) -> status -> results, results --only-failed,
                    results --export-format csv
  eval_run_compare  start -> start again with --solution-id + --project-id
                    (no redeploy) -> list -> compare --compare-to

Checks (``--check``):

  artifacts      Local eval assets: the `product-match` exact-match evaluator and
                 the `Product Checks` set holding the expected data points.
  results        LIVE. Re-reads `run results` for the run id the agent recorded
                 in eval-evidence/run-start.json, so a fabricated results file
                 cannot pass: `correct` must score 1.0 and `wrong-on-purpose`
                 below 1.0, both Completed.
  failed-only    eval-evidence/failed-only.json is a successful results envelope
                 whose rows are exactly the failing data point.
  export         A `bpmn-eval-results-*.csv` export exists and lists both cases.
  runs           LIVE. `run list` for the set reports both run ids the agent
                 recorded (run-1.json, run-2.json), distinct and Completed.
  compare        eval-evidence/compare.json is a successful compare envelope that
                 references both recorded run ids.

``--data-points`` sets which cases `artifacts` requires (default: both).

Envelope field names follow Flow's `check_eval_run.py`: tolerant of the flat
`Data` list and of `Data.Results`, and of a per-row `Score` or `EvaluatorScores`.
Standard library only (the suite's CI job installs pytest and nothing else).
"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import sys
from pathlib import Path
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from _shared.bpmn_check import find_bpmn_file  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    CheckFailure,
    get_ci,
    parse_json_output,
    payload_data,
    run_cli,
)

PROJECT = "ProductCheck"
SET_NAME = "Product Checks"
EVALUATOR = "product-match"
EXACT_MATCH_TYPE_ID = "uipath-exact-match"
EXPECTED = {"correct": 42, "wrong-on-purpose": 41}
PASSING = "correct"
FAILING = "wrong-on-purpose"
EVIDENCE = Path("eval-evidence")
CLI_TIMEOUT = 180

RUN_ID_KEYS = ("evalSetRunId", "evalsetrunid", "runId", "id")
ROW_NAME_KEYS = ("DataPoint", "DataPointName", "EvaluationName", "Name", "name")
TERMINAL_OK = "completed"


def fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


# --------------------------------------------------------------------------- #
# JSON helpers
# --------------------------------------------------------------------------- #


def load_json(path: Path) -> Any:
    if not path.is_file():
        fail(f"missing {path}")
    try:
        return parse_json_output(path.read_text(encoding="utf-8"), str(path))
    except (CheckFailure, OSError) as exc:
        fail(str(exc))
    return None  # unreachable


def find_key(value: Any, keys: tuple[str, ...]) -> Any:
    """First value of any of ``keys`` (case-insensitive), searching depth-first."""
    wanted = [k.casefold() for k in keys]
    for key in wanted:
        hit = _walk_for(value, key)
        if hit not in (None, ""):
            return hit
    return None


def _walk_for(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        for candidate, item in value.items():
            if str(candidate).casefold() == key and not isinstance(item, (dict, list)):
                return item
        for item in value.values():
            hit = _walk_for(item, key)
            if hit not in (None, ""):
                return hit
    elif isinstance(value, list):
        for item in value:
            hit = _walk_for(item, key)
            if hit not in (None, ""):
                return hit
    return None


def run_id_from(path: Path) -> str:
    doc = load_json(path)
    run_id = find_key(get_ci(doc, "Data", doc), RUN_ID_KEYS[:2]) or find_key(
        doc, RUN_ID_KEYS
    )
    if not run_id:
        fail(f"{path} carries no evalSetRunId")
    return str(run_id)


def is_success(doc: Any) -> bool:
    return str(get_ci(doc, "Result", "")).casefold() == "success"


def result_rows(doc: Any) -> list[dict]:
    data = get_ci(doc, "Data")
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        for key in ("Results", "DataPoints", "Rows"):
            rows = get_ci(data, key)
            if isinstance(rows, list):
                return [r for r in rows if isinstance(r, dict)]
    return []


def row_name(row: dict) -> str:
    for key in ROW_NAME_KEYS:
        value = get_ci(row, key)
        if isinstance(value, str) and value:
            return value
    return "?"


def row_scores(row: dict) -> list[float]:
    scores: list[float] = []
    flat = get_ci(row, "Score")
    if isinstance(flat, (int, float)) and not isinstance(flat, bool):
        scores.append(float(flat))
    es = get_ci(row, "EvaluatorScores")
    entries = es.values() if isinstance(es, dict) else es if isinstance(es, list) else []
    for entry in entries:
        value = get_ci(entry, "Score") if isinstance(entry, dict) else entry
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            scores.append(float(value))
    return scores


def rows_by_name(rows: list[dict]) -> dict[str, dict]:
    return {row_name(r): r for r in rows}


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #


def _local_docs() -> list[tuple[Path, dict]]:
    out = []
    for p in Path(".").rglob("*.json"):
        if EVIDENCE in p.parents:
            continue
        try:
            value = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(value, dict):
            out.append((p, value))
    return out


def _evaluator_name(doc: dict) -> Any:
    config = doc.get("evaluatorConfig")
    if isinstance(config, dict) and config.get("name"):
        return config["name"]
    return doc.get("name") or doc.get("id")


def _expected_product(case: dict) -> Any:
    expected = case.get("expectedOutput") or case.get("expected")
    if isinstance(expected, str):
        try:
            expected = json.loads(expected)
        except json.JSONDecodeError:
            return None
    return get_ci(expected, "product") if isinstance(expected, dict) else None


def check_artifacts(data_points: list[str]) -> None:
    docs = _local_docs()
    evaluator = next(
        (
            p
            for p, d in docs
            if _evaluator_name(d) == EVALUATOR
            and d.get("evaluatorTypeId") == EXACT_MATCH_TYPE_ID
        ),
        None,
    )
    if evaluator is None:
        fail(f'no evaluator JSON named "{EVALUATOR}" with evaluatorTypeId "{EXACT_MATCH_TYPE_ID}"')
    print(f"OK: evaluator {evaluator}")

    eval_set = next(
        (
            (p, d)
            for p, d in docs
            if d.get("name") == SET_NAME and isinstance(d.get("evaluations"), list)
        ),
        None,
    )
    if eval_set is None:
        fail(f'no eval-set JSON named "{SET_NAME}"')
    cases = {c.get("name"): c for c in eval_set[1]["evaluations"] if isinstance(c, dict)}
    for name in data_points:
        case = cases.get(name)
        if case is None:
            fail(f'eval set "{SET_NAME}" has no data point "{name}"; got {sorted(map(str, cases))}')
        product = _expected_product(case)
        if product != EXPECTED[name]:
            fail(f'data point "{name}" expects product={product!r}, want {EXPECTED[name]}')
    print(f"OK: eval set {eval_set[0]} holds {data_points} with the expected outputs")


def _project_dir() -> Path:
    return Path(find_bpmn_file(PROJECT)).resolve().parent


def _live(arguments: list[str], label: str) -> Any:
    try:
        completed = run_cli(arguments, timeout=CLI_TIMEOUT)
        payload, _ = payload_data(completed, label)
    except FileNotFoundError:
        fail("uip CLI not found on PATH; the live check cannot run")
    except CheckFailure as exc:
        fail(str(exc))
    return payload


def check_results() -> None:
    run_id = run_id_from(EVIDENCE / "run-start.json")
    payload = _live(
        [
            "uip", "maestro", "bpmn", "eval", "run", "results", run_id,
            "--set", SET_NAME, "--path", str(_project_dir()),
        ],
        f"eval run results {run_id}",
    )
    verify_scores(payload)
    print(f"OK: live results for run {run_id}: {PASSING}=1.0, {FAILING}<1.0")


def verify_scores(payload: Any) -> None:
    rows = rows_by_name(result_rows(payload))
    missing = [n for n in (PASSING, FAILING) if n not in rows]
    if missing:
        fail(f"results lack rows for {missing}; got {sorted(rows)}")
    for name, row in ((PASSING, rows[PASSING]), (FAILING, rows[FAILING])):
        status = str(get_ci(row, "Status", "")).casefold()
        if status != TERMINAL_OK:
            fail(f"{name!r}: Status={get_ci(row, 'Status')!r} (expected Completed)")
        if not row_scores(row):
            fail(f"{name!r}: no numeric score (row keys: {sorted(row)})")
    if any(s != 1.0 for s in row_scores(rows[PASSING])):
        fail(f"{PASSING!r} scored {row_scores(rows[PASSING])}, expected 1.0")
    if all(s >= 1.0 for s in row_scores(rows[FAILING])):
        fail(f"{FAILING!r} scored {row_scores(rows[FAILING])}; the evaluator could not tell 41 from 42")


def check_failed_only() -> None:
    doc = load_json(EVIDENCE / "failed-only.json")
    if not is_success(doc):
        fail(f"failed-only.json is not a successful envelope: {get_ci(doc, 'Message')!r}")
    names = sorted(rows_by_name(result_rows(doc)))
    if names != [FAILING]:
        fail(f"failed-only.json should list only {FAILING!r}, got {names}")
    print(f"OK: failed-only results list just {FAILING!r}")


def check_export() -> None:
    exports = sorted(glob.glob("**/bpmn-eval-results-*.csv", recursive=True))
    if not exports:
        fail("no bpmn-eval-results-*.csv export found")
    for path in exports:
        with open(path, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
        text = "\n".join(",".join(r) for r in rows)
        if len(rows) >= 3 and PASSING in text and FAILING in text:
            print(f"OK: {path} has a header and rows for both cases")
            return
    fail(f"no CSV export lists both {PASSING!r} and {FAILING!r}: {exports}")


def _run_ids(payload: Any) -> dict[str, str]:
    """Map run id -> status from a `run list` envelope."""
    data = get_ci(payload, "Data")
    items = data if isinstance(data, list) else get_ci(data, "Runs") or get_ci(data, "Items") or []
    out: dict[str, str] = {}
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        run_id = find_key(item, RUN_ID_KEYS)
        if run_id:
            out[str(run_id)] = str(get_ci(item, "Status", ""))
    return out


def check_runs() -> None:
    first = run_id_from(EVIDENCE / "run-1.json")
    second = run_id_from(EVIDENCE / "run-2.json")
    if first == second:
        fail(f"run-1.json and run-2.json record the same run id {first}")
    payload = _live(
        ["uip", "maestro", "bpmn", "eval", "run", "list", "--set", SET_NAME, "--path", str(_project_dir())],
        "eval run list",
    )
    verify_run_list(payload, first, second)
    print(f"OK: run list reports runs {first} and {second}, both Completed")


def verify_run_list(payload: Any, first: str, second: str) -> None:
    runs = _run_ids(payload)
    for run_id in (first, second):
        if run_id not in runs:
            fail(f"run list does not report run {run_id}; got {sorted(runs)}")
        if runs[run_id].casefold() != TERMINAL_OK:
            fail(f"run {run_id} status is {runs[run_id]!r}, expected Completed")


def check_compare() -> None:
    first = run_id_from(EVIDENCE / "run-1.json")
    second = run_id_from(EVIDENCE / "run-2.json")
    doc = load_json(EVIDENCE / "compare.json")
    if not is_success(doc):
        fail(f"compare.json is not a successful envelope: {get_ci(doc, 'Message')!r}")
    text = json.dumps(doc)
    missing = [r for r in (first, second) if r not in text]
    if missing:
        fail(f"compare.json does not reference run(s) {missing}")
    print(f"OK: compare.json compares {first} and {second}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        required=True,
        choices=("artifacts", "results", "failed-only", "export", "runs", "compare"),
    )
    parser.add_argument("--data-points", nargs="+", default=list(EXPECTED), choices=list(EXPECTED))
    args = parser.parse_args()
    {
        "artifacts": lambda: check_artifacts(args.data_points),
        "results": check_results,
        "failed-only": check_failed_only,
        "export": check_export,
        "runs": check_runs,
        "compare": check_compare,
    }[args.check]()


if __name__ == "__main__":
    main()
