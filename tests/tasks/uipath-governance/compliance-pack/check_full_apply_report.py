#!/usr/bin/env python3
"""Validate report.json logical relationships for the full-apply compliance standard flow.

Handles two known schema variants the agent may produce:
  Schema A: {standard: {packId, ...}, posture: {notAppliedSettings, coveragePct, ...}, applyAction: {...}}
  Schema B: {packId, standard: str, posture: {settingsAppliedBefore, highImpactGapsBefore, ...}, applyAttempt: {...}}

Key validations (exits 1 on critical violations):
  1. Pack ID is iso-42001-2023 (top-level packId or standard.packId)
  2. posture section exists with at least one recognizable numeric field
  3. Some apply-related tracking exists (applyAction, applyAttempt, outcome, enable_called)
  4. If posture indicates gaps AND no backend error → an apply action was attempted

Field-presence issues are warnings (exits 0); logical violations exit 1.
"""
import json
import sys

REPORT = "report.json"

try:
    with open(REPORT, encoding="utf-8") as f:
        r = json.load(f)
except FileNotFoundError:
    print(f"FAIL: {REPORT} not found", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"FAIL: {REPORT} is not valid JSON — {e}", file=sys.stderr)
    sys.exit(1)

failures = []
warnings = []

# ── 1. pack_id — check standard.packId (Schema A) or top-level packId (Schema B) ──
pack_id = None
standard = r.get("standard")
if isinstance(standard, dict):
    pack_id = standard.get("packId")
if pack_id is None:
    pack_id = r.get("packId")

if pack_id not in ("iso-42001-2023", "iso-42001"):
    failures.append(
        f"pack_id is '{pack_id}' — expected 'iso-42001-2023' "
        "(checked standard.packId and top-level packId)"
    )

# ── 2. posture section ────────────────────────────────────────────────────────
posture = r.get("posture")
if not isinstance(posture, dict):
    failures.append("posture section is missing or not an object")
    posture = {}

def _num(d, *keys):
    for k in keys:
        v = d.get(k)
        if isinstance(v, (int, float)):
            return v
    return None

not_applied = _num(posture,
    "notAppliedSettings",      # Schema A
    "settingsNotApplied",
)
applied_before = _num(posture,
    "appliedSettings",         # Schema A
    "settingsApplied",
    "settingsAppliedBefore",   # Schema B
)
coverage_pct = _num(posture,
    "coveragePct",             # Schema A
    "coveragePercentBefore",   # Schema B
)
high_impact_gaps = _num(posture, "highImpactGapsBefore")  # Schema B only

# At least one numeric posture field must exist
if all(v is None for v in (not_applied, applied_before, coverage_pct, high_impact_gaps)):
    failures.append(
        "posture section has no recognized numeric fields — "
        "expected notAppliedSettings, appliedSettings, coveragePct, "
        "settingsAppliedBefore, or highImpactGapsBefore"
    )

# ── 3. Apply tracking ─────────────────────────────────────────────────────────
apply_action = r.get("applyAction") or {}
apply_attempt = r.get("applyAttempt") or {}
has_apply_tracking = any([
    apply_action,
    apply_attempt,
    r.get("outcome") is not None,
    r.get("enable_called") is not None,
])
if not has_apply_tracking:
    warnings.append(
        "no apply-tracking field found — "
        "expected applyAction, applyAttempt, outcome, or enable_called"
    )

# ── 4. Causal: gaps present AND no backend error → enable must have been called ──
# Determine if the tenant had gaps before the run
has_gaps = (
    (isinstance(not_applied, (int, float)) and not_applied > 0) or
    (isinstance(applied_before, (int, float)) and applied_before == 0) or
    (isinstance(coverage_pct, (int, float)) and coverage_pct == 0) or
    (isinstance(high_impact_gaps, (int, float)) and high_impact_gaps > 0)
)

# Detect backend error (agent should not be blamed for server failures)
apply_attempt_str = str(apply_attempt).lower()
has_backend_error = (
    "error" in apply_attempt_str or
    "500" in apply_attempt_str or
    "failure" in apply_attempt_str or
    "failed" in str(r.get("outcome", "")).lower()
)

enable_was_called = (
    apply_action.get("performed") is True or
    bool(apply_attempt.get("command")) or
    r.get("enable_called") is True
)

if has_gaps and not has_backend_error and not enable_was_called:
    failures.append(
        "posture showed gaps before the run but no enable was attempted "
        "(expected state enable to be called)"
    )

# ── Report ────────────────────────────────────────────────────────────────────
for w in warnings:
    print(f"WARNING: {w}")

if failures:
    for f_msg in failures:
        print(f"FAIL: {f_msg}", file=sys.stderr)
    sys.exit(1)

print(
    f"OK: report.json valid — pack={pack_id}, "
    f"coverage={coverage_pct}%, "
    f"notApplied={not_applied}, "
    f"appliedBefore={applied_before}, "
    f"has_apply_tracking={has_apply_tracking}, "
    f"has_gaps={has_gaps}, "
    f"has_backend_error={has_backend_error}"
)
sys.exit(0)
