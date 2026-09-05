#!/usr/bin/env python3
"""Best-effort cleanup: delete the secret-rotate smoke's app by EXACT name.

Exact-name (not substring) so parallel runs (-jN) cannot delete a sibling test's
app. Always exits 0.
"""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_ext_app_rotate: %(message)s")
logger = logging.getLogger(__name__)

APP = "ce-identity-smoke-rotateapp"


def main():
    data = run_cli(["admin", "external-apps", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list external apps — skipping cleanup")
        return
    for a in data.get("Data", []):
        if (a.get("Name") or a.get("name") or "") == APP:
            cid = a.get("ClientId") or a.get("clientId") or a.get("Id") or a.get("id")
            if cid:
                logger.info("Deleting external app clientId=%s (name=%s)", cid, APP)
                run_cli(["admin", "external-apps", "delete", cid])


main()
sys.exit(0)
