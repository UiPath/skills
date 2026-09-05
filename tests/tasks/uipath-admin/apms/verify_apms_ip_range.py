#!/usr/bin/env python3
"""Verify an IP allowlist entry against the live organization.

  APMS_CHECK             present | updated | absent | expiring (required)
  APMS_SEED_KEY          seed.json key holding this run's expected entry — its
                         `name` and `cidrs` come from there, so concurrent runs
                         check their own objects and nothing else (required)
  APMS_EXPECT_CIDR_INDEX which of the seeded `cidrs` the entry must carry now,
                         for `updated` (default: all of them must be present)
  APMS_EXPIRES_IN_DAYS   the entry must carry an ExpiresAt roughly this many days
                         out (±2 days); only expiring entries carry the field

Modes:
  present  — an entry with the expected name exists on the org, allowing the
             expected CIDR (or every CIDR in APMS_RANGE_CIDRS).
  updated  — the seeded entry id still exists and now carries the expected name
             and/or CIDR. The agent did not create this entry, so the changed
             field can only come from a real update.
  absent   — the seeded entry id is gone (the agent deleted it, by id or by
             CIDR). A missing state file is an ERROR, not a pass: with no seed
             the id would be trivially absent and a do-nothing agent would score.
  expiring — an entry with the expected name exists and its ExpiresAt lands in
             the requested window, proving the expiry was actually applied.

Exits 0 on success, 1 on failure.
"""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import fail, ok, poll, run_cli, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_apms_ip_range: %(message)s")


def ranges() -> list[dict] | None:
    """Current allowlist, or None when the list call itself failed."""
    data = run_cli(["admin", "ip-restriction", "ip-ranges", "list"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data") or []


def check_present(name: str, cidr: str, cidrs: list[str]):
    def found():
        rows = ranges()
        if rows is None:
            return None
        return next((r for r in rows if (r.get("Name") or "") == name), None)

    entry = poll(found)
    if not entry:
        rows = ranges()
        seen = [r.get("Name") for r in (rows or [])]
        fail(f"no allowlist entry named '{name}' on the organization — entries found: {seen}")

    named = [r for r in (ranges() or []) if (r.get("Name") or "") == name]
    allowed = {r.get("IpNetwork") for r in named}
    if cidrs:
        missing = [c for c in cidrs if c not in allowed]
        if missing:
            fail(f"entry '{name}' does not allow {missing} — networks stored under that name: {sorted(allowed)}")
        ok(f"allowlist entries named '{name}' cover {sorted(allowed)} on the organization")
        return
    if cidr and cidr not in allowed:
        fail(f"entry '{name}' allows {sorted(allowed)}, expected {cidr!r}")
    ok(f"allowlist entry '{name}' ({entry.get('IpNetwork')}) present on the organization")


def check_expiring(name: str, days: int):
    """An expiry only shows up on entries created with one, so this proves it applied."""
    from datetime import datetime, timezone

    def found():
        rows = ranges()
        if rows is None:
            return None
        return next((r for r in rows if (r.get("Name") or "") == name and r.get("ExpiresAt")), None)

    entry = poll(found)
    if not entry:
        rows = ranges() or []
        fail(f"no expiring allowlist entry named '{name}' — entries found: "
             f"{[(r.get('Name'), r.get('ExpiresAt')) for r in rows]}")

    raw = str(entry.get("ExpiresAt")).replace("Z", "+00:00")
    try:
        expires = datetime.fromisoformat(raw)
    except ValueError:
        fail(f"entry '{name}' carries an unparseable ExpiresAt: {entry.get('ExpiresAt')!r}")
    delta_days = (expires - datetime.now(timezone.utc)).total_seconds() / 86400
    if abs(delta_days - days) > 2:
        fail(f"entry '{name}' expires in {delta_days:.1f} days, expected about {days}")
    ok(f"allowlist entry '{name}' expires {entry.get('ExpiresAt')} (~{delta_days:.0f} days out)")


def check_updated(state: dict, expected_name: str, expected_cidr: str):
    if not state or not state.get("ids"):
        fail("the entry to update was never seeded for this run (no seed.json entry)")
    state = {"id": state["ids"][0], "name": state.get("name")}

    def updated():
        rows = ranges()
        if rows is None:
            return None
        entry = next((r for r in rows if r.get("Id") == state["id"]), None)
        if not entry:
            return None
        if expected_name and (entry.get("Name") or "") != expected_name:
            return None
        if expected_cidr and (entry.get("IpNetwork") or "") != expected_cidr:
            return None
        return entry

    entry = updated() or poll(updated)
    if not entry:
        rows = ranges() or []
        current = next((r for r in rows if r.get("Id") == state["id"]), None)
        if not current:
            fail(f"seeded entry id={state['id']} is gone — it was deleted instead of updated")
        fail(f"seeded entry still reads name={current.get('Name')!r} network={current.get('IpNetwork')!r}; "
             f"expected name={expected_name or '(unchanged)'!r} network={expected_cidr or '(unchanged)'!r}")
    ok(f"seeded entry id={state['id']} updated: name={entry.get('Name')!r} network={entry.get('IpNetwork')!r}")


def check_absent(state: dict):
    if not state or not state.get("ids"):
        fail("the entry to delete was never seeded for this run (no seed.json entry)")
    state = {"id": state["ids"][0], "name": state.get("name")}

    present = None
    for _ in range(3):
        rows = ranges()
        if rows is None:
            present = None
            continue
        present = any(r.get("Id") == state["id"] for r in rows)
        if not present:
            break

    if present is None:
        fail("could not list IP ranges to confirm the deletion")
    if present:
        fail(f"seeded entry '{state.get('name')}' (id={state['id']}) is still on the organization")
    ok(f"seeded entry '{state.get('name')}' (id={state['id']}) deleted")


def main():
    check = (os.environ.get("APMS_CHECK") or "").strip()
    seed_key = (os.environ.get("APMS_SEED_KEY") or "").strip()
    days = (os.environ.get("APMS_EXPIRES_IN_DAYS") or "").strip()
    idx = (os.environ.get("APMS_EXPECT_CIDR_INDEX") or "").strip()
    if not seed_key:
        fail("APMS_SEED_KEY must be set — it names this run's expected entry in seed.json")
    state = seed_entry(seed_key)
    if not state:
        fail(f"seed.json has no '{seed_key}' entry — nothing was seeded or requested for this run")
    name, cidrs = state.get("name"), state.get("cidrs") or []

    if check == "present":
        check_present(name, "", cidrs)
    elif check == "updated":
        target = cidrs[int(idx)] if idx else (cidrs[-1] if cidrs else "")
        check_updated(state, name, target)
    elif check == "absent":
        check_absent(state)
    elif check == "expiring":
        if not days:
            fail("APMS_EXPIRES_IN_DAYS is required for APMS_CHECK=expiring")
        check_expiring(name, int(days))
    else:
        fail("APMS_CHECK must be one of present | updated | absent | expiring")


main()
