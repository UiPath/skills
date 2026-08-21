#!/usr/bin/env python3
"""Verify the IXP full-lifecycle e2e artifacts.

Grades artifact integrity, NOT whether the model's F1 improved. On the ~3-doc
fixture set a single flipped prediction moves a field's F1 by a large fraction,
so a small regression tolerance is noise the agent doesn't control, not signal.
Asserts: artifacts present & well-formed; Fields[] populated; ModelVersion an int
and not backwards; target field resolves to a numeric F1 in both snapshots. The F1
delta is printed but never gates. An advanced version with byte-identical Fields[]
only WARNs — on the coarse fixture a genuine retrain can flip no prediction, so
identical metrics are the same noise this check refuses to grade, and it cannot be
told from a counter bump by the artifacts alone. "Did the agent run the improve loop"
(update-prompts, two metric fetches, publish) is graded by the command_executed criteria.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NoReturn

CWD = Path.cwd()


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
    """Accept the full CLI response ({Code, Data: {...}}) or a pre-unwrapped Data payload."""
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
    """Field's F1 as a float; None if missing or non-numeric."""
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

    # Not a failure: if retrain hadn't completed, a genuine second fetch can match the first.
    if improved == baseline:
        log_warn("improved_metrics == baseline_metrics — retrain may not have completed (acceptable) or no real second measurement (not)")

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
        log_fail(f"ModelVersion went backwards ({baseline_version} -> {improved_version}) — improved_metrics is stale, from another project, or swapped")
    if improved_version == baseline_version:
        log_info(f"ModelVersion unchanged at {baseline_version} — no new version yet (acceptable)")
    else:
        log_info(f"ModelVersion advanced {baseline_version} -> {improved_version}")
        # Advanced version + byte-identical Fields[] *can* be a copied snapshot with the counter
        # bumped, but on the ~3-doc fixture it is far more often a genuine second measurement where
        # the retrain flipped no prediction, so every field's F1 is unchanged — the same coarse-metric
        # noise this check deliberately refuses to grade (see docstring / #1814). The artifacts alone
        # cannot tell the two apart; whether the agent actually re-measured is enforced by the
        # command_executed criteria (get-metrics >=2, update-prompts, publish). So warn, don't fail.
        if improved_fields == baseline_fields:
            log_warn(f"ModelVersion advanced {baseline_version} -> {improved_version} but Fields[] is identical to baseline — retrain likely flipped no prediction on the coarse fixture; re-measurement is graded by the command_executed criteria")

    # Chosen field must resolve to a numeric F1 in both snapshots (catches a hallucinated
    # field_id or truncated metrics), regardless of which way F1 moved.
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

    # Informational only — F1 direction is noise on ~3 docs (see docstring).
    delta = impr_f1 - base_f1
    log_info(f"target field F1: {base_f1:.3f} -> {impr_f1:.3f} (delta {delta:+.3f}) [not graded]")

    log_info("full-lifecycle artifacts present, well-formed, and coherent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
