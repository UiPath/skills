#!/usr/bin/env python3
"""Best-effort cleanup: delete all external apps named 'e2e-federated-app'.

Always exits 0 — failures here never affect pass/fail.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, find_all

logging.basicConfig(level=logging.INFO, format="cleanup_fedapp: %(message)s")
logger = logging.getLogger(__name__)


def main():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list external apps — skipping cleanup")
        return

    matches = find_all(data, "e2e-federated-app", ["name"])
    if not matches:
        logger.info("No 'e2e-federated-app' found — nothing to clean up")
        return

    for app in matches:
        client_id = app.get("id")
        if not client_id:
            continue
        logger.info("Deleting external app (id=%s)", client_id)
        result = run_cli(["admin", "external-apps", "delete", client_id])
        if result:
            logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
        else:
            logger.warning("Delete call returned no result for id=%s", client_id)


main()
sys.exit(0)
