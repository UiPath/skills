#!/usr/bin/env python3
"""Pre-run seed for the pat-revoke smoke: free PAT slots, then create the marker
PAT the agent will be asked to revoke. Records the created PAT id to a state file
so the verify step can prove the seed existed (and fail — not falsely pass — if
it did not). Always exits 0 (best-effort seed)."""

import datetime
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="setup_revoke_pat: %(message)s")
logger = logging.getLogger(__name__)

MARKER = "ce-identity-smoke-revoke-pat"
# Distinctive markers only — a bare "smoke" would revoke real PATs on the org.
FREE_MARKERS = ("ce-identity-smoke", "e2e-test-pat")
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_revoke_pat_seed.txt")


def main():
    # Clear any stale state from a prior run in this container.
    try:
        os.remove(STATE_FILE)
    except OSError:
        pass

    # The tenant caps a user at 5 PATs — revoke lingering test PATs to free a slot.
    data = run_cli(["admin", "pat", "list"])
    if data and data.get("Result") == "Success":
        for t in data.get("Data", []):
            desc = (t.get("Description") or t.get("description") or "").lower()
            if any(m in desc for m in FREE_MARKERS):
                tid = t.get("Id") or t.get("id")
                if tid:
                    run_cli(["admin", "pat", "revoke", tid])

    # Seed the PAT the agent will revoke. Expiration is computed ~6 months out so
    # the date never falls into the past (would fail create) and stays within the
    # org's PAT-lifetime cap (reference tokens must expire within 360 days).
    expiration = (datetime.date.today() + datetime.timedelta(days=180)).isoformat()
    res = run_cli(["admin", "pat", "create", "--description", MARKER,
                   "--scope", "OR.Folders.Read", "--expiration", expiration])
    if not res or res.get("Result") != "Success":
        logger.warning("Seed PAT create failed (cap full of real PATs?): %s", res)
        return

    # Resolve the created PAT's id and record it as authoritative proof of the seed.
    lst = run_cli(["admin", "pat", "list"])
    seed_id = None
    if lst and lst.get("Result") == "Success":
        for t in lst.get("Data", []):
            if (t.get("Description") or t.get("description") or "") == MARKER:
                seed_id = t.get("Id") or t.get("id")
                break
    if seed_id:
        with open(STATE_FILE, "w") as f:
            f.write(seed_id)
        logger.info("Seeded revoke-target PAT id=%s", seed_id)
    else:
        logger.warning("Could not resolve seeded PAT id")


main()
sys.exit(0)
