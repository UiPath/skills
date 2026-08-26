#!/usr/bin/env python3
"""Verify the seeded marker user was deleted by the agent.

Reads the seed user id recorded by setup_delete_user.py. If the seed was never
created (no state file) this is an ERROR, not a pass — otherwise a do-nothing
agent would "pass" because the user is trivially absent. Given a real seed id,
asserts that exact user is now gone from the tenant.
"""

import logging
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_user_deleted: %(message)s")

SEARCH = "ce-identity-delete"
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_delete_user_seed.txt")


def id_present(o, sid):
    """True if any record anywhere in o carries Id/id == sid (shape-tolerant)."""
    if isinstance(o, dict):
        if (o.get("Id") or o.get("id")) == sid:
            return True
        return any(id_present(v, sid) for v in o.values())
    if isinstance(o, list):
        return any(id_present(v, sid) for v in o)
    return False


def main():
    if not os.path.exists(STATE_FILE):
        fail("seed user was never created (no state file) — cannot validate deletion")
    with open(STATE_FILE) as f:
        seed_id = f.read().strip()
    if not seed_id:
        fail("seed user id missing — cannot validate deletion")

    # Primary signal: the seed id must vanish from the marker-scoped listing.
    # --search (not an unfiltered list) keeps this reliable against user-list
    # pagination on a busy org. Poll generously to absorb delete-propagation lag
    # (deletes are eventually-consistent, at least as slow as invites).
    present = None
    for i in range(6):
        data = run_cli(["admin", "users", "list", "--search", SEARCH], timeout=15)
        if not data or data.get("Result") != "Success":
            fail("could not list users to confirm deletion")
        present = id_present(data.get("Data", []), seed_id)
        if not present:
            break
        if i < 5:
            time.sleep(5)

    if present:
        fail(f"seed user id={seed_id} still present — agent did not delete it")

    # Guard the one false-pass the search can't see: if the agent renamed the
    # user (changing the email out of the marker prefix) instead of deleting it,
    # the id drops from the search but the user still exists. A direct get-by-id
    # confirms real deletion. Retry so a single transient CLI failure (which,
    # like a genuine not-found, surfaces as None) cannot silently skip the guard:
    # a live renamed user surfaces on a retry, while a real not-found stays None
    # across all attempts (and the search above already proved the CLI is up).
    for attempt in range(3):
        got = run_cli(["admin", "users", "get", seed_id], timeout=15)
        if got and got.get("Result") == "Success" and id_present(got, seed_id):
            fail(f"seed user id={seed_id} still exists (get-by-id) — agent modified it, did not delete")
        if got is not None:
            break  # definitive response with no live record for the id → deleted
        if attempt < 2:
            time.sleep(3)

    ok(f"seed user id={seed_id} successfully deleted (absent from tenant)")


main()
