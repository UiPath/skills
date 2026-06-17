#!/usr/bin/env python3
"""Validate coverage.json contains real API data from a live tenant.

Used only in live e2e tests (not sandbox tests where CLI auth fails).

Checks:
  1. coverage.json exists and is valid JSON
  2. Has the expected PascalCase top-level structure (Data.Summary, Data.DeploymentPolicies)
  3. Data.Summary has NewCount and DeploymentPolicyCount fields
  4. Data.DeploymentPolicies is a non-empty list
  5. Each policy entry has Status field (new or in-place)

Exits 1 on any structural violation.
"""

import json
import sys

import os
import glob

# Search for coverage.json — agent may save it to SESSION_TEMP, TASK_DIR, or cwd.
# In Docker CI the sandbox working dir is TASK_DIR; locally it may be SESSION_TEMP.
_candidates = [
    "coverage.json",
    os.path.join(os.environ.get("TASK_DIR", ""), "coverage.json"),
    os.path.join(os.environ.get("SESSION_TEMP", ""), "coverage.json"),
    os.path.join(os.environ.get("TMPDIR", ""), "coverage.json"),
]
# Also glob for coverage.json under common temp prefixes created by the agent
_candidates += glob.glob("/tmp/compliance-*/coverage.json")
_candidates += glob.glob(os.path.join(os.environ.get("TEMP", ""), "compliance-*", "coverage.json"))

COVERAGE = "coverage.json"
for candidate in _candidates:
    if candidate and os.path.exists(candidate):
        COVERAGE = candidate
        break

try:
    with open(COVERAGE, encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"FAIL: {COVERAGE} not found — was state coverage run and output saved?", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"FAIL: {COVERAGE} is not valid JSON — {e}", file=sys.stderr)
    sys.exit(1)

failures = []

# ── Result field ──────────────────────────────────────────────────────────────
result = data.get("Result")
if result == "Failure":
    msg = data.get("Message", "unknown error")
    print(f"FAIL: CLI reported failure — {msg}", file=sys.stderr)
    sys.exit(1)

# ── Data presence ─────────────────────────────────────────────────────────────
payload = data.get("Data")
if not isinstance(payload, dict):
    failures.append("Data field is missing or not an object")
else:
    # Summary
    summary = payload.get("Summary") or payload.get("summary")
    if not isinstance(summary, dict):
        failures.append("Data.Summary is missing or not an object")
    else:
        new_count = summary.get("NewCount") if "NewCount" in summary else summary.get("newCount")
        total = summary.get("DeploymentPolicyCount") if "DeploymentPolicyCount" in summary else summary.get("deploymentPolicyCount")
        if new_count is None:
            failures.append("Data.Summary.NewCount is missing")
        if total is None:
            failures.append("Data.Summary.DeploymentPolicyCount is missing")

    # DeploymentPolicies
    policies = payload.get("DeploymentPolicies") or payload.get("deploymentPolicies")
    if not isinstance(policies, list):
        failures.append("Data.DeploymentPolicies is missing or not a list")
    elif len(policies) == 0:
        failures.append("Data.DeploymentPolicies is empty — no products in coverage response")
    else:
        for i, p in enumerate(policies[:3]):  # spot-check first 3
            status = p.get("Status") or p.get("status")
            if status not in ("new", "in-place"):
                failures.append(
                    f"DeploymentPolicies[{i}].Status is '{status}' — expected 'new' or 'in-place'"
                )

if failures:
    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    sys.exit(1)

policy_count = len(policies) if isinstance(policies, list) else 0
print(
    f"OK: coverage.json is valid — "
    f"{policy_count} product policies, "
    f"NewCount={new_count}, DeploymentPolicyCount={total}"
)
sys.exit(0)
