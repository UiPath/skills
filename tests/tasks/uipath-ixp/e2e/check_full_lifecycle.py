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
    """Return the `Metrics` dict from a get-metrics response.

    The Design-Time API shape is `{Code, Data: {Metrics: {...}}}`, where
    `Metrics` holds `ModelVersion`, the overall `ProjectScore`, and
    `FieldMetrics.{FieldGroupsMetrics, FieldsMetrics}`. Also accepts a
    pre-unwrapped `Data` ({Metrics: {...}}) or the `Metrics` dict itself."""
    data = blob.get("Data") if isinstance(blob.get("Data"), dict) else blob
    metrics = data.get("Metrics") if isinstance(data.get("Metrics"), dict) else data
    if isinstance(metrics, dict) and "FieldMetrics" in metrics and "ModelVersion" in metrics:
        return metrics
    log_fail(f"{label} is not a recognizable IxpProjectsGetMetrics payload (expected Metrics.FieldMetrics + ModelVersion)")


def fields_by_id(metrics: dict, label: str) -> dict[str, dict]:
    """Flatten `Metrics.FieldMetrics.FieldsMetrics` — keyed by group name,
    then by field id ({group: {field_id: {...}}}) — into {field_id: metrics}."""
    field_metrics = metrics.get("FieldMetrics")
    if not isinstance(field_metrics, dict):
        log_fail(f"{label} has missing or malformed FieldMetrics")
    per_group = field_metrics.get("FieldsMetrics")
    if not isinstance(per_group, dict) or not per_group:
        log_fail(f"{label} has missing or malformed FieldMetrics.FieldsMetrics")
    flattened: dict[str, dict] = {}
    for group_fields in per_group.values():
        if isinstance(group_fields, dict):
            flattened.update(group_fields)
    if not flattened:
        log_fail(f"{label} has no fields under FieldMetrics.FieldsMetrics")
    return flattened


def read_f1(field: dict) -> float | None:
    """Parse a field's F1 (`F1Score.Value`) as a float; None if missing or
    non-numeric. Callers that gate on F1 must handle None explicitly."""
    score = field.get("F1Score")
    raw = score.get("Value") if isinstance(score, dict) else None
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

    baseline_fields = fields_by_id(baseline, "baseline_metrics")
    improved_fields = fields_by_id(improved, "improved_metrics")
    log_info(f"baseline fields: {len(baseline_fields)}, improved fields: {len(improved_fields)}")

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

    base_target = baseline_fields.get(field_id)
    impr_target = improved_fields.get(field_id)
    if base_target is None:
        log_fail(f"target field_id {field_id} not present in baseline FieldsMetrics")
    if impr_target is None:
        log_fail(f"target field_id {field_id} not present in improved FieldsMetrics")

    base_f1 = read_f1(base_target)
    impr_f1 = read_f1(impr_target)
    if base_f1 is None or impr_f1 is None:
        log_fail(f"target field {field_id} has missing or non-numeric F1Score.Value (baseline={base_target.get('F1Score')!r}, improved={impr_target.get('F1Score')!r})")
    delta = impr_f1 - base_f1
    print(f"target field F1: {base_f1:.3f} -> {impr_f1:.3f} (delta {delta:+.3f})")
    if delta < TARGET_REGRESSION_LIMIT:
        log_fail(f"target field F1 regressed by more than {-TARGET_REGRESSION_LIMIT:.2f} ({delta:+.3f})")
    log_info("target field F1 did not regress significantly")

    return 0


if __name__ == "__main__":
    sys.exit(main())
