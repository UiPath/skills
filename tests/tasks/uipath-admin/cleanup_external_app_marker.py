#!/usr/bin/env python3
"""Best-effort cleanup: delete external apps whose name contains the smoke marker.

Covers the create-external-app, federated-credentials, and secret-rotate smokes
(all use a 'ce-identity-smoke-*' app name). Always exits 0.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_external_app_marker: %(message)s")
logger = logging.getLogger(__name__)

MARKER_SUBSTR = "ce-identity-smoke"


def main():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list external apps — skipping cleanup")
        return
    for a in data.get("Data", []):
        name = a.get("Name") or a.get("name") or a.get("DisplayName") or ""
        if MARKER_SUBSTR in name:
            cid = a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
            if cid:
                logger.info("Deleting external app clientId=%s (name=%r)", cid, name)
                run_cli(["admin", "external-apps", "delete", cid])


main()
sys.exit(0)
