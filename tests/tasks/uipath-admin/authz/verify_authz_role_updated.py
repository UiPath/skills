#!/usr/bin/env python3
"""Verify the agent updated the pre-seeded role — read back from the tenant.

  AUTHZ_SEED_KEY     state file written by setup_authz_role.py (required)
  AUTHZ_EXPECT_DESCRIPTION  description the update must have applied (required)
  AUTHZ_EXPECT_PERMISSION   action the role must still grant after the update
                            (optional — `roles update` rewrites the action list,
                            so a careless update can silently drop it)

The seeded role id comes from the state file: the agent did not create this role,
so a matching description can only mean a real `roles update` landed. A missing
state file is an ERROR, not a pass — without a seed there is nothing to update.

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
from admin_helpers import fail, ok, poll, role_get, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_authz_role_updated: %(message)s")


def main():
    seed_key = (os.environ.get("AUTHZ_SEED_KEY") or "").strip()
    expected = (os.environ.get("AUTHZ_EXPECT_DESCRIPTION") or "").strip()
    permission = (os.environ.get("AUTHZ_EXPECT_PERMISSION") or "").strip()
    if not seed_key or not expected:
        fail("AUTHZ_SEED_KEY and AUTHZ_EXPECT_DESCRIPTION must be set")

    state = seed_entry(seed_key)
    if not state or not state.get("id"):
        fail("the role to update was never seeded (no seed.json entry) — cannot validate the update")

    role = poll(lambda: role_get(state["id"]))
    if not role:
        fail(f"seeded role '{state.get('name')}' (id={state['id']}) is gone — "
             "it was deleted instead of updated")

    actual = (role.get("Description") or "").strip()
    if actual != expected:
        seeded = (state.get("description") or "").strip()
        hint = " (still the seeded description — no update landed)" if actual == seeded else ""
        fail(f"role '{state.get('name')}' description is {actual!r}, expected {expected!r}{hint}")

    if permission:
        actions = [a.get("Name") for a in (role.get("ActionDetails") or [])]
        if permission not in actions:
            fail(f"update dropped {permission} from role '{state.get('name')}' — actions now: {actions}")

    ok(f"seeded role '{state.get('name')}' (id={state['id']}) updated: description={actual!r}")


main()
