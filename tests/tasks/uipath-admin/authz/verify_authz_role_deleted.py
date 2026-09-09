#!/usr/bin/env python3
"""Verify the agent deleted the pre-seeded role — read back from the tenant.

  AUTHZ_SEED_KEY  state file written by setup_authz_role.py (required)

The seeded role id comes from the state file. A missing state file is an ERROR,
not a pass: without a real seed the role would be trivially absent and a
do-nothing agent would score.

The role list must be retrievable for the check to mean anything — an
unreachable tenant fails the criterion rather than reading as "deleted".

Exits 0 on success, 1 on failure.
"""

import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import fail, ok, run_cli, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_authz_role_deleted: %(message)s")


def still_present(role_id: str, name: str) -> bool | None:
    """True/False when the tenant answers; None when the list call itself failed."""
    data = run_cli([
        "admin", "authorization", "roles", "list",
        "--role-type", "Custom", "--filter", name, "--limit", "100",
    ])
    if not data or data.get("Result") != "Success":
        return None
    payload = data.get("Data") or {}
    results = payload.get("Results", []) if isinstance(payload, dict) else (payload or [])
    return any((r.get("Id") or r.get("id")) == role_id for r in results)


def main():
    seed_key = (os.environ.get("AUTHZ_SEED_KEY") or "").strip()
    if not seed_key:
        fail("AUTHZ_SEED_KEY must be set")

    state = seed_entry(seed_key)
    if not state or not state.get("id"):
        fail("the role to delete was never seeded (no seed.json entry) — cannot validate the deletion")

    present = None
    for attempt in range(4):
        present = still_present(state["id"], state.get("name") or "")
        if present is False:
            break
        if attempt < 3:
            time.sleep(5)

    if present is None:
        fail("could not list roles to confirm the deletion")
    if present:
        fail(f"seeded role '{state.get('name')}' (id={state['id']}) is still on the tenant — "
             "the agent did not delete it")
    ok(f"seeded role '{state.get('name')}' (id={state['id']}) deleted")


main()
