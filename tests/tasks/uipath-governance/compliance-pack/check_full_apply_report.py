#!/usr/bin/env python3
"""Validate report.json logical relationships for the full-apply compliance standard flow.

The prompt deliberately does NOT dictate the report.json schema — it asks the agent to
record three facts (pack identity, posture counts, whether apply was performed) and leaves
the structure AND the naming convention to the agent. Observed real runs vary widely:
  - camelCase:  {pack:{packId}, posture:{beforeApply:{newCount, inPlaceCount}}, applyResult:"Success"}
  - snake_case: {pack:{pack_id}, posture_before_apply:{settings_not_applied, coverage_pct}, apply_performed:true}
  - flat / Schema A/B/C from earlier runs.

So this validator is SHAPE- AND CASING-AGNOSTIC. It walks the whole JSON tree, NORMALIZES
every key (lowercase, strip non-alphanumerics → `coverage_pct`, `coveragePct`, `Coverage-Pct`
all collapse to `coveragepct`), and verifies the three facts exist *somewhere*. It must fail
ONLY on real defects, never on a different-but-valid layout or naming style.

Critical checks (exit 1):
  1. The ISO 42001 pack id appears somewhere (iso-42001-2023 or iso-42001).
  2. CROSS-VALIDATION against the real API data: the authoritative posture counts
     from coverage.json (Data.Summary.NewCount and DeploymentPolicyCount — the raw
     `state coverage` response, separately validated as real by
     check_coverage_real_data.py) must BOTH appear as numbers in report.json. This
     makes report.json non-self-gradeable: the agent cannot fabricate a passing
     summary without having actually run `state coverage` and transcribed its real
     numbers. (Replaces the earlier "any posture-ish number exists" check, which an
     agent could satisfy with invented values.)
  3. If posture shows gaps existed AND there was no backend error → an apply must be tracked
     as performed (the agent must not silently skip applying when gaps exist).

Soft checks (warning, exit 0):
  - No apply-tracking field found at all.
"""
import glob
import json
import os
import re
import sys

REPORT = "report.json"


def _load_coverage():
    """Locate + load coverage.json (the real state-coverage API response) and return
    (new_count, deployment_policy_count), or (None, None, reason) if unavailable.

    Mirrors check_coverage_real_data.py's candidate search so it finds the file
    wherever the agent saved it (cwd, TASK_DIR, SESSION_TEMP, temp dirs)."""
    candidates = [
        "coverage.json",
        os.path.join(os.environ.get("TASK_DIR", ""), "coverage.json"),
        os.path.join(os.environ.get("SESSION_TEMP", ""), "coverage.json"),
        os.path.join(os.environ.get("TMPDIR", ""), "coverage.json"),
    ]
    candidates += glob.glob("/tmp/compliance-*/coverage.json")
    candidates += glob.glob("/tmp/tmp.*/coverage.json")
    candidates += glob.glob(os.path.join(os.environ.get("HOME", ""), "compliance-*", "coverage.json"))
    candidates += glob.glob(os.path.join(os.environ.get("TEMP", ""), "compliance-*", "coverage.json"))

    path = next((c for c in candidates if c and os.path.exists(c)), None)
    if not path:
        return None, None, "coverage.json not found"
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return None, None, f"coverage.json unreadable — {e}"

    summary = (data.get("Data") or {}).get("Summary") or (data.get("Data") or {}).get("summary") or {}
    new_count = summary.get("NewCount", summary.get("newCount"))
    total = summary.get("DeploymentPolicyCount", summary.get("deploymentPolicyCount"))
    if new_count is None or total is None:
        return None, None, "coverage.json missing Summary.NewCount / DeploymentPolicyCount"
    return new_count, total, None

try:
    with open(REPORT, encoding="utf-8") as f:
        r = json.load(f)
except FileNotFoundError:
    print(f"FAIL: {REPORT} not found", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"FAIL: {REPORT} is not valid JSON — {e}", file=sys.stderr)
    sys.exit(1)


def _norm(s):
    """Collapse a key to a casing/separator-agnostic token: 'coverage_pct' -> 'coveragepct'."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


# ── Flatten the whole JSON tree into normalized (key, value, parent_key) triples ──
_triples = []   # (norm_key, value, norm_parent_key) for every dict entry at any depth
_strings = []   # every string scalar anywhere


def _walk(obj, parent=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            nk = _norm(k)
            _triples.append((nk, v, parent))
            _walk(v, nk)
    elif isinstance(obj, list):
        for item in obj:
            _walk(item, parent)
    elif isinstance(obj, str):
        _strings.append(obj)


_walk(r)


def _nums_for(*names):
    """All numeric (non-bool) values whose normalized key matches any of `names`, anywhere."""
    wanted = {_norm(n) for n in names}
    return [v for nk, v, _ in _triples
            if nk in wanted and isinstance(v, (int, float)) and not isinstance(v, bool)]


def _has_key(*names):
    wanted = {_norm(n) for n in names}
    return any(nk in wanted for nk, _, _ in _triples)


def _truthy_for(*names):
    """True if any matching key holds a truthy bool / success-ish value, anywhere."""
    wanted = {_norm(n) for n in names}
    for nk, v, _ in _triples:
        if nk not in wanted:
            continue
        if v is True:
            return True
        if isinstance(v, str) and v.strip().lower() in ("success", "succeeded", "applied", "true", "ok", "done"):
            return True
        if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
            return True
        if isinstance(v, (dict, list)) and v:  # non-empty applyAction / applyResult object
            return True
    return False


failures = []
warnings = []

# ── 1. Pack id appears somewhere ────────────────────────────────────────────────
pack_ok = any(("iso-42001-2023" in s or s.strip().lower() in ("iso-42001", "iso-42001-2023"))
              for s in _strings)
if not pack_ok:
    sample = [s for s in _strings if "iso" in s.lower()][:3]
    failures.append(
        "ISO 42001 pack id not found anywhere in report.json "
        f"(expected 'iso-42001-2023'; iso-ish strings seen: {sample or 'none'})"
    )

# ── 2. Cross-validate posture counts against the real coverage.json API data ─────
# Collect every number anywhere in report.json, then require the authoritative
# counts from coverage.json to be present — the agent must have transcribed real
# `state coverage` output, not invented a plausible-looking summary.
all_report_nums = {v for _, v, _ in _triples
                   if isinstance(v, (int, float)) and not isinstance(v, bool)}
cov_new, cov_total, cov_err = _load_coverage()
if cov_err:
    failures.append(
        f"cannot cross-validate report.json against real API data — {cov_err}. "
        "The full-apply flow must save the state coverage response to coverage.json."
    )
else:
    if cov_new not in all_report_nums:
        failures.append(
            f"report.json does not contain the real 'not applied' count from coverage.json "
            f"(NewCount={cov_new}). Numbers present in report.json: {sorted(all_report_nums)[:12]}. "
            "The posture counts in report.json must match the live state coverage response."
        )
    if cov_total not in all_report_nums:
        failures.append(
            f"report.json does not contain the real total from coverage.json "
            f"(DeploymentPolicyCount={cov_total}). Numbers present: {sorted(all_report_nums)[:12]}."
        )

# Posture-count buckets below are still needed for the causal apply check (section 4).
not_applied_vals = _nums_for(
    "notAppliedSettings", "settingsNotApplied", "deploymentPoliciesNew",
    "newCount", "gaps", "totalGaps", "notApplied", "missingSettings",
    "settingsMissing", "remainingSettings", "settingsRemaining",
)
applied_vals = _nums_for(
    "appliedSettings", "settingsApplied", "settingsAppliedBefore",
    "deploymentPoliciesInPlace", "inPlaceCount",
)
total_vals = _nums_for("deploymentPolicyCount", "policyCount", "totalSettings", "total", "totalControls")
coverage_vals = _nums_for("coveragePct", "coveragePercentBefore", "coveragePercent", "coverage")
high_gap_vals = _nums_for("highImpactGapsBefore", "highImpactGaps")
clause_gap_vals = _nums_for("clausesWithGaps")

# ── 3. Apply tracking ───────────────────────────────────────────────────────────
has_apply_tracking = _has_key(
    "applyPerformed", "applyResult", "applyAction", "applyAttempt",
    "outcome", "enableCalled", "performed", "applyOutcome", "verificationResult",
)
if not has_apply_tracking:
    warnings.append(
        "no apply-tracking field found — expected applyPerformed, applyResult, "
        "applyAction, applyAttempt, outcome, or enable_called"
    )

# ── 4. Causal: gaps existed AND no backend error → apply must be tracked as performed ──
has_gaps = bool(
    any(v > 0 for v in not_applied_vals)
    or any(v > 0 for v in high_gap_vals)
    or any(v > 0 for v in clause_gap_vals)
    or any(v == 0 for v in coverage_vals)
    # inPlace < total (some product not yet applied)
    or (applied_vals and total_vals and min(applied_vals) < max(total_vals))
)

# Backend error: a server failure the agent is not to blame for.
_blob = " ".join(_strings).lower()
_status_error = any(
    isinstance(v, str) and any(w in v.lower() for w in ("error", "failed", "failure"))
    for nk, v, _ in _triples if nk in ("applyresult", "outcome", "applyoutcome", "status")
)
has_backend_error = (
    "retrywillnotfix" in _blob
    or " 500" in _blob or "500 " in _blob or "http 500" in _blob or "status 500" in _blob
    or "internal server error" in _blob
    or _status_error
)

enable_performed = (
    _truthy_for("applyPerformed", "performed", "enableCalled")
    or _truthy_for("applyResult", "outcome", "applyOutcome")
    or _truthy_for("applyAction", "applyAttempt", "verificationResult")
)

if has_gaps and not has_backend_error and not enable_performed:
    failures.append(
        "posture showed gaps existed but no apply was tracked as performed "
        "(expected state enable to be called and recorded). "
        f"not_applied={not_applied_vals}, applied={applied_vals}, coverage={coverage_vals}"
    )

# ── Report ──────────────────────────────────────────────────────────────────────
for w in warnings:
    print(f"WARNING: {w}")

if failures:
    for f_msg in failures:
        print(f"FAIL: {f_msg}", file=sys.stderr)
    sys.exit(1)

print(
    "OK: report.json valid — "
    f"pack_id_found={pack_ok}, "
    f"coverage_cross_check: NewCount={cov_new} & DeploymentPolicyCount={cov_total} both present in report.json, "
    f"has_apply_tracking={has_apply_tracking}, "
    f"has_gaps={has_gaps}, "
    f"has_backend_error={has_backend_error}, "
    f"enable_performed={enable_performed}"
)
sys.exit(0)
