#!/usr/bin/env python3
"""Verify the IXP full-lifecycle e2e task drove the improve-a-model workflow FOR REAL.

Run from the sandbox working directory. Exits 0 on success, 1 on failure.

Scope: this grades the AGENT's behavior and the INTEGRITY of the artifacts it
captured — NOT whether the model's F1 went up. Whether a single prompt tweak plus
one retrain raises a field's F1 on the ~3-document fixture set is a
non-deterministic model outcome the agent does not control: over 3 docs F1 is
quantized in ~0.17-0.33 steps, so normal retrain noise makes any F1-direction
gate flaky (a single flipped prediction swings it past any tolerance finer than a
step). So we assert only what a correct run genuinely controls:
  - artifacts present and well-formed (baseline metrics, improved metrics, target field);
  - metrics coherent — Fields[] populated, ModelVersion an int that did not go
    backwards (backwards => stale/swapped/other-project artifacts);
  - the agent targeted a REAL field — its chosen field_id resolves to a row with
    a numeric F1 in BOTH the baseline and improved metrics.
The target field's F1 delta is printed for human debugging but never gates.

The behavioral half of "did the agent run the improve loop" (update-prompts ran,
metrics fetched twice, etc.) is graded by the task's command_executed criteria;
this script covers artifact integrity.
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

    # Best-effort integrity hint. Not a failure: when retrain has not completed
    # (the task lets the agent capture current metrics and proceed rather than
    # wait indefinitely), a genuine second fetch legitimately matches the first.
    if improved == baseline:
        log_warn("improved_metrics matches baseline_metrics exactly — retrain likely had not completed at capture time (acceptable) or no real second measurement was taken (not)")

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
        log_info(f"ModelVersion unchanged at {baseline_version} — retrain produced no new version yet (acceptable)")
    else:
        log_info(f"ModelVersion advanced {baseline_version} -> {improved_version}")

    # The agent must have targeted a REAL, measurable field: its chosen field_id
    # has to resolve to a row with a numeric F1 in both snapshots. This catches a
    # hallucinated/mismatched field_id or truncated metrics — without asserting
    # anything about which direction the F1 moved.
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

    # Informational only — NOT a gate. On ~3 docs an F1 direction/delta is noise,
    # not a signal the agent controls (see module docstring).
    delta = impr_f1 - base_f1
    log_info(f"target field F1: {base_f1:.3f} -> {impr_f1:.3f} (delta {delta:+.3f}) [informational, not graded]")

    log_info("full-lifecycle artifacts are present, well-formed, and coherent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
