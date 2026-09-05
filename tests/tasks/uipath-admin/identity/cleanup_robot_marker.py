#!/usr/bin/env python3
"""Best-effort cleanup: delete robot accounts whose name contains the smoke marker.

Always exits 0. Uses the PascalCase Name/Id keys the tenant returns.
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

logging.basicConfig(level=logging.INFO, format="cleanup_robot_marker: %(message)s")
logger = logging.getLogger(__name__)

MARKER = "ce-identity-smoke-bot"


def main():
    data = run_cli(["admin", "robot-accounts", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list robot accounts — skipping cleanup")
        return
    for r in data.get("Data", []):
        name = r.get("Name") or r.get("name") or ""
        if MARKER in name:
            rid = r.get("Id") or r.get("id")
            if rid:
                logger.info("Deleting robot account id=%s", rid)
                run_cli(["admin", "robot-accounts", "delete", rid])


main()
sys.exit(0)
