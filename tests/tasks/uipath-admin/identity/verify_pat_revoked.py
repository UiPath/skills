#!/usr/bin/env python3
"""Verify the seeded marker PAT was revoked by the agent.

Reads the seed PAT id recorded by setup_revoke_pat.py. If the seed was never
created (no state file) this is an ERROR, not a pass — otherwise a do-nothing
agent would "pass" because the token is trivially absent. Given a real seed id,
asserts that exact PAT is now gone from the tenant.
"""

import logging
import os
import sys
import tempfile
import time

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_pat_revoked: %(message)s")

STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_revoke_pat_seed.txt")


def main():
    if not os.path.exists(STATE_FILE):
        fail("seed PAT was never created (no state file) — cannot validate revocation")
    seed_id = open(STATE_FILE).read().strip()
    if not seed_id:
        fail("seed PAT id missing — cannot validate revocation")

    present = None
    for i in range(4):
        data = run_cli(["admin", "pat", "list"])
        if not data or data.get("Result") != "Success":
            fail("could not list PATs to confirm revocation")
        present = any((t.get("Id") or t.get("id")) == seed_id for t in data.get("Data", []))
        if not present:
            break
        time.sleep(5)

    if present:
        fail(f"seed PAT id={seed_id} still present — agent did not revoke it")
    ok(f"seed PAT id={seed_id} successfully revoked (absent from tenant)")


main()
