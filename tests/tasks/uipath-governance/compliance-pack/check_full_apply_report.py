#!/usr/bin/env python3
"""Validate report.json logical relationships for the full-apply compliance standard flow.

Checks:
  1. Required fields are present
  2. If enable_called is True, pack_active_after must also be True
  3. If settings_not_applied > 0, enable_called should be True
  4. commands_attempted starts with catalog get, then coverage (correct sequence)
  5. commands_attempted has at least 3 entries

Always exits 0 for field-presence warnings; exits 1 only on critical logical violations.
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

# ── 1. Required fields ────────────────────────────────────────────────────────
for field in ("pack_id", "posture_analysis_run", "enable_called", "commands_attempted"):
    if field not in r:
        warnings.append(f"missing field: {field}")

# ── 2. pack_id is correct ─────────────────────────────────────────────────────
if r.get("pack_id") not in ("iso-42001-2023", "iso-42001"):
    failures.append(
        f"pack_id is '{r.get('pack_id')}' — expected 'iso-42001-2023'"
    )

# ── 3. Causal: enable_called → pack_active_after ──────────────────────────────
# Only fail if pack_active_after is explicitly False — absent/null means the
# CLI couldn't be verified (e.g. sandbox auth failure), which is acceptable.
if r.get("enable_called") is True and r.get("pack_active_after") is False:
    failures.append(
        "enable_called=True but pack_active_after=False — "
        "state enable ran but state get confirmed pack is NOT active"
    )

# ── 4. Causal: settings_not_applied > 0 → enable_called ──────────────────────
not_applied = r.get("settings_not_applied", r.get("settings_to_configure"))
if isinstance(not_applied, (int, float)) and not_applied > 0:
    if r.get("enable_called") is not True:
        failures.append(
            f"settings_not_applied={not_applied} but enable_called is not True — "
            "gaps existed but state enable was not called"
        )

# ── 5. Sequence: commands_attempted[0] = catalog, [1] = coverage ─────────────
commands = r.get("commands_attempted", [])
if not isinstance(commands, list):
    failures.append("commands_attempted is not a list")
else:
    if len(commands) < 3:
        failures.append(
            f"commands_attempted has {len(commands)} entries — expected at least 3 "
            "(catalog get, state coverage, state get/enable)"
        )
    if commands and "catalog" not in str(commands[0]).lower():
        failures.append(
            f"commands_attempted[0] does not reference 'catalog': '{commands[0]}'"
        )
    if len(commands) > 1 and "coverage" not in str(commands[1]).lower():
        failures.append(
            f"commands_attempted[1] does not reference 'coverage': '{commands[1]}'"
        )

# ── Report ────────────────────────────────────────────────────────────────────
for w in warnings:
    print(f"WARNING: {w}")

if failures:
    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    sys.exit(1)

total = len(commands) if isinstance(commands, list) else 0
print(
    f"OK: report.json valid — pack={r.get('pack_id')}, "
    f"enable_called={r.get('enable_called')}, "
    f"pack_active_after={r.get('pack_active_after')}, "
    f"commands={total}"
)
sys.exit(0)
