#!/usr/bin/env python3
"""Pre-run seed for the pat-revoke smoke: free PAT slots, then create the marker
PAT the agent will be asked to revoke. Always exits 0 (best-effort seed)."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="setup_revoke_pat: %(message)s")
logger = logging.getLogger(__name__)

MARKER = "ce-identity-smoke-revoke-pat"
FREE_MARKERS = ("ce-identity-smoke", "e2e-test-pat", "smoke")


def main():
    # The tenant caps a user at 5 PATs — revoke lingering test PATs to free a slot.
    data = run_cli(["admin", "pat", "list"])
    if data and data.get("Result") == "Success":
        for t in data.get("Data", []):
            desc = (t.get("Description") or t.get("description") or "").lower()
            if any(m in desc for m in FREE_MARKERS):
                tid = t.get("Id") or t.get("id")
                if tid:
                    run_cli(["admin", "pat", "revoke", tid])

    # Seed the PAT the agent will revoke.
    res = run_cli(["admin", "pat", "create", "--description", MARKER,
                   "--scope", "OR.Folders.Read", "--expiration", "2027-01-15"])
    logger.info("Seeded revoke-target PAT '%s': %s", MARKER, (res or {}).get("Result"))


main()
sys.exit(0)
