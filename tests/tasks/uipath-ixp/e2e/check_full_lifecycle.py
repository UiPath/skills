#!/usr/bin/env python3
"""Verify artifacts produced by the IXP full-lifecycle e2e task.

Run from the sandbox working directory. Exits 0 on success, 1 on failure.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NoReturn

CWD = Path.cwd()

# F1 delta; negative = regression. Coarse because this task scores over only
# ~3 documents, where a single flipped prediction swings F1 by ~0.33.
TARGET_REGRESSION_LIMIT = -0.15  # the field the agent chose to improve


def log_fail(msg: str) -> NoReturn:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def log_info(msg: str) -> None:
    print(f"INFO: {msg}")


def log_warn(msg: str) -> None:
    print(f"WARN: {msg}")


def load_json(name: str) -> dict:
    path = CWD / name
    if not path.exists():
        log_fail(f"{name} not found in {CWD}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        log_fail(f"{name} is not valid JSON: {exc}")
    if not isinstance(data, dict):
        log_fail(f"{name} is not a JSON object (got {type(data).__name__})")
    return data


def unwrap_metrics(blob: dict, label: str) -> dict:
    """Accept either the full CLI response ({Code, Data: {...}}) or
    a pre-unwrapped Data payload. Returns the Data-shaped dict."""
    if "Data" in blob and isinstance(blob["Data"], dict):
        return blob["Data"]
    if "Fields" in blob and "ModelVersion" in blob:
        return blob
    log_fail(f"{label} is neither a full IxpProjectsGetMetrics response nor an unwrapped Data payload")


def find_field(fields: list[dict], field_id: str) -> dict | None:
    for f in fields:
        if f.get("FieldId") == field_id:
            return f
    return None


def read_f1(field: dict) -> float | None:
    """Parse a field's F1 as a float; None if missing or non-numeric.
    Callers that gate on F1 must handle None explicitly."""
    raw = field.get("F1")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def main() -> int:
    target = load_json("target_field.json")
    field_id = target.get("field_id")
    if not field_id or not isinstance(field_id, str):
        log_fail(f"target_field.json missing string 'field_id': {target}")
    log_info(f"target field: {target.get('name')} ({field_id})")

    baseline = unwrap_metrics(load_json("baseline_metrics.json"), "baseline_metrics.json")
    improved = unwrap_metrics(load_json("improved_metrics.json"), "improved_metrics.json")

    # Best-effort integrity hint. Not a failure: when retrain produces no new
    # training signal, a genuine second fetch legitimately matches the first.
    if improved == baseline:
        log_warn("improved_metrics matches baseline_metrics exactly — verify a real second measurement was taken (acceptable only if retrain was a no-op)")

    baseline_fields = baseline.get("Fields")
    improved_fields = improved.get("Fields")
    if not isinstance(baseline_fields, list) or not baseline_fields:
        log_fail("baseline_metrics has missing or malformed Fields[]")
    if not isinstance(improved_fields, list) or not improved_fields:
        log_fail("improved_metrics has missing or malformed Fields[]")
    log_info(f"baseline Fields: {len(baseline_fields)}, improved Fields: {len(improved_fields)}")

    baseline_version = baseline.get("ModelVersion")
    improved_version = improved.get("ModelVersion")
    if not isinstance(baseline_version, int) or not isinstance(improved_version, int):
        log_fail(f"ModelVersion not an int (baseline={baseline_version!r}, improved={improved_version!r})")
    if improved_version < baseline_version:
        log_fail(f"ModelVersion went backwards (baseline={baseline_version}, improved={improved_version}) — improved_metrics is stale, from another project, or the artifacts are swapped")
    if improved_version == baseline_version:
        log_info(f"ModelVersion unchanged at {baseline_version} — re-label produced no new training signal (acceptable)")
    else:
        log_info(f"ModelVersion advanced {baseline_version} -> {improved_version}")

    base_target = find_field(baseline_fields, field_id)
    impr_target = find_field(improved_fields, field_id)
    if base_target is None:
        log_fail(f"target field_id {field_id} not present in baseline Fields[]")
    if impr_target is None:
        log_fail(f"target field_id {field_id} not present in improved Fields[]")

    base_f1 = read_f1(base_target)
    impr_f1 = read_f1(impr_target)
    if base_f1 is None or impr_f1 is None:
        log_fail(f"target field {field_id} has missing or non-numeric F1 (baseline={base_target.get('F1')!r}, improved={impr_target.get('F1')!r})")
    delta = impr_f1 - base_f1
    print(f"target field F1: {base_f1:.3f} -> {impr_f1:.3f} (delta {delta:+.3f})")
    if delta < TARGET_REGRESSION_LIMIT:
        log_fail(f"target field F1 regressed by more than {-TARGET_REGRESSION_LIMIT:.2f} ({delta:+.3f})")
    log_info("target field F1 did not regress significantly")

    return 0


if __name__ == "__main__":
    sys.exit(main())
