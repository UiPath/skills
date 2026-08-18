#!/usr/bin/env python3
"""Best-effort teardown for the external-app maintain e2e: delete the marker apps
under any of their names (pre-rename, post-rename, retired).

Exact-name matching (not substring) so a parallel run (-jN) cannot sweep a
sibling test's app — several fixtures share the 'ce-identity-' prefix. Always
exits 0 — failures here never affect pass/fail.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_extapp_maintain: %(message)s")
logger = logging.getLogger(__name__)

APPS = (
    "ce-identity-extapp-active",
    "ce-identity-extapp-consolidated",
    "ce-identity-extapp-retired",
)


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
sys.exit(0)
