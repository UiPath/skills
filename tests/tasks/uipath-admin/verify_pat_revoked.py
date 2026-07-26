#!/usr/bin/env python3
"""Verify the seeded marker PAT is gone after the agent revoked it.

The marker PAT is created in pre_run (setup_revoke_pat.py); this asserts it is
absent from the tenant's PAT list. Exits 1 (fail) if still present or the list
cannot be read.
"""

import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_pat_revoked: %(message)s")

MARKER = "ce-identity-smoke-revoke-pat"


def present():
    data = run_cli(["admin", "pat", "list"])
    if not data or data.get("Result") != "Success":
        return None  # cannot confirm
    return any((t.get("Description") or t.get("description") or "") == MARKER
               for t in data.get("Data", []))


def main():
    p = None
    for i in range(4):
        p = present()
        if p is None:
            fail("could not list PATs to confirm revocation")
        if not p:
            break
        time.sleep(5)
    if p:
        fail(f"PAT '{MARKER}' still present — agent did not revoke it")
    ok(f"PAT '{MARKER}' successfully revoked (absent from tenant)")


main()
