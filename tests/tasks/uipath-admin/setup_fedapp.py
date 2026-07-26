#!/usr/bin/env python3
"""Pre-run seed for the federated-credentials smoke: (re)create a confidential
external app the agent will attach a federated credential to. Always exits 0."""

import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="setup_fedapp: %(message)s")
logger = logging.getLogger(__name__)

APP = "ce-identity-smoke-fedapp"
# The federated-credentials endpoint rejects a just-created app with
# "Client not found in partition" for a while after creation; give it time to
# propagate before the agent attaches a credential.
SETTLE_SECONDS = 75


def main():
    data = run_cli(["admin", "external-apps", "list"])
    if data and data.get("Result") == "Success":
        for a in data.get("Data", []):
            if (a.get("Name") or a.get("name") or "") == APP:
                cid = a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
                if cid:
                    run_cli(["admin", "external-apps", "delete", cid])

    # Confidential app (default) — supports federated credentials.
    res = run_cli(["admin", "external-apps", "create", APP, "--app-scope", "OR.Folders,OR.Jobs"])
    logger.info("Seeded fedapp '%s': %s", APP, (res or {}).get("Result"))
    if res and res.get("Result") == "Success":
        logger.info("Waiting %ds for the app to propagate to the federation partition...", SETTLE_SECONDS)
        time.sleep(SETTLE_SECONDS)


main()
sys.exit(0)
