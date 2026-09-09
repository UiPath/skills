#!/usr/bin/env python3
"""Verify the agent revoked the pre-seeded role assignment — read back from the tenant.

  AUTHZ_SEED_KEY  state file written by setup_authz_assignment.py

The seeded assignment id, scope path and identity all come from the state file. A
missing state file is an ERROR, not a pass: with no seeded grant the id would be
trivially absent and a do-nothing agent would score.

The assignment list must be retrievable for the check to mean anything — an
unreachable tenant fails the criterion rather than reading as "revoked".

Exits 0 on success, 1 on failure.
"""

import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import fail, ok, run_cli, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_authz_assignment_deleted: %(message)s")


def still_present(assignment_id: str, identity_id: str, scope_path: str) -> bool | None:
    """True/False when the tenant answers; None when the list call itself failed."""
    data = run_cli([
        "admin", "authorization", "roles", "assignments", "list",
        "--scope-path", scope_path, "--identity-id", identity_id, "--limit", "10",
    ])
    if not data or data.get("Result") != "Success":
        return None
    payload = data.get("Data") or {}
    groups = payload.get("Results", []) if isinstance(payload, dict) else (payload or [])
    return any(
        a.get("Id") == assignment_id
        for g in groups for a in (g.get("RoleAssignmentDtos") or [])
    )


def main():
    seed_key = (os.environ.get("AUTHZ_SEED_KEY") or "").strip()
    if not seed_key:
        fail("AUTHZ_SEED_KEY must be set")

    state = seed_entry(seed_key)
    if not state or not state.get("id"):
        fail("the assignment to revoke was never seeded (no seed.json entry) — "
             "cannot validate the revocation")

    present = None
    for attempt in range(4):
        present = still_present(state["id"], state["identity"], state["scope"])
        if present is False:
            break
        if attempt < 3:
            time.sleep(5)

    if present is None:
        fail("could not list role assignments to confirm the revocation")
    if present:
        fail(f"seeded grant of '{state.get('role')}' (id={state['id']}) is still on the tenant "
             f"at {state['scope']} — the agent did not revoke it")
    ok(f"seeded grant of '{state.get('role')}' (id={state['id']}) revoked at {state['scope']}")


main()
