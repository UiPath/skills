#!/usr/bin/env python3
"""Best-effort teardown for the external-app maintain e2e: delete the marker apps
under any of their names (pre-rename, post-rename, retired).

Exact-name matching (not substring) so a parallel run (-jN) cannot sweep a
sibling test's app — several fixtures share the 'ce-identity-' prefix. Always
exits 0 — failures here never affect pass/fail.
"""

import json
import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_extapp_maintain: %(message)s")
logger = logging.getLogger(__name__)

APPS = (
    "ce-identity-extapp-active",
    "ce-identity-extapp-consolidated",
    "ce-identity-extapp-retired",
)


STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_extapp_maintain_seed.json")


def sweep_seeded_ids():
    """Delete the seeded apps BY ID as well as by name.

    Name-only cleanup cannot see the very failure mode the verify now detects: an
    app renamed instead of deleted (zz-archived-app) is invisible to both this
    cleanup and the next run's pre-delete, so it is orphaned permanently on a
    shared org — and setup creates these apps confidential, so the orphan retains
    a live client secret. The ids are already in the state file.
    """
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError):
        return
    for key in ("active_client_id", "retired_client_id"):
        cid = state.get(key)
        if not cid:
            continue
        got = run_cli(["admin", "external-apps", "get", str(cid)])
        if got and got.get("Result") == "Success":
            logger.info("Deleting seeded app by id %s (survived name-based cleanup)", cid)
            run_cli(["admin", "external-apps", "delete", str(cid)])


def main():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list external apps — skipping cleanup")
        return
    for a in data.get("Data", []):
        name = a.get("Name") or a.get("name") or a.get("DisplayName") or ""
        if name not in APPS:
            continue
        cid = a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
        if cid:
            logger.info("Deleting external app '%s' (clientId=%s)", name, cid)
            run_cli(["admin", "external-apps", "delete", cid])


main()
sweep_seeded_ids()
sys.exit(0)
