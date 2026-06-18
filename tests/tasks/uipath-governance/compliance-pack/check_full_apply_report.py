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
  2. At least one recognizable posture-count number appears somewhere (named field OR any
     number nested under a posture/coverage/gap/setting/clause/policy container).
  3. If posture shows gaps existed AND there was no backend error → an apply must be tracked
     as performed (the agent must not silently skip applying when gaps exist).

Soft checks (warning, exit 0):
  - No apply-tracking field found at all.
"""
import json
import re
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

# ── 2. Posture counts appear somewhere ──────────────────────────────────────────
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

posture_nums = (not_applied_vals + applied_vals + total_vals
                + coverage_vals + high_gap_vals + clause_gap_vals)

# Structural fallback: accept any number nested under (or named like) a posture-ish
# container, so novel field names the agent invents still count.
_POSTURE_CONTAINERS = ("posture", "coverage", "gap", "setting", "clause", "policies", "policy",
                       "summary", "before", "after", "compliance", "result", "score")
if not posture_nums:
    posture_nums = [
        v for nk, v, par in _triples
        if isinstance(v, (int, float)) and not isinstance(v, bool)
        and (any(c in nk for c in _POSTURE_CONTAINERS) or any(c in par for c in _POSTURE_CONTAINERS))
    ]

if not posture_nums:
    failures.append(
        "no recognizable posture-count number found anywhere in report.json — "
        "expected at least one count under a posture/coverage/gap/setting/clause section "
        "(e.g. newCount / inPlaceCount / settings_not_applied / coverage_pct / clauses_with_gaps)"
    )

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
    f"posture_nums={posture_nums[:8]}, "
    f"has_apply_tracking={has_apply_tracking}, "
    f"has_gaps={has_gaps}, "
    f"has_backend_error={has_backend_error}, "
    f"enable_performed={enable_performed}"
)
sys.exit(0)
