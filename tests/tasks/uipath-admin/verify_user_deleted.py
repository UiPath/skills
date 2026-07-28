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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_user_deleted: %(message)s")

SEARCH = "ce-identity-delete"
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_delete_user_seed.txt")


def main():
    if not os.path.exists(STATE_FILE):
        fail("seed user was never created (no state file) — cannot validate deletion")
    seed_id = open(STATE_FILE).read().strip()
    if not seed_id:
        fail("seed user id missing — cannot validate deletion")

    present = None
    for i in range(4):
        data = run_cli(["admin", "users", "list", "--search", SEARCH])
        if not data or data.get("Result") != "Success":
            fail("could not list users to confirm deletion")
        present = any((u.get("Id") or u.get("id")) == seed_id for u in data.get("Data", []))
        if not present:
            break
        time.sleep(5)

    if present:
        fail(f"seed user id={seed_id} still present — agent did not delete it")
    ok(f"seed user id={seed_id} successfully deleted (absent from tenant)")


main()
