#!/usr/bin/env python3
"""Best-effort cleanup: delete the lifecycle-smoke user by marker email."""

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

logging.basicConfig(level=logging.INFO, format="cleanup_lifecycle_user: %(message)s")
logger = logging.getLogger(__name__)

MARKER_EMAIL = "ce-identity-lifecycle@example.com"


def main():
    data = run_cli(["admin", "users", "list", "--search", "ce-identity-lifecycle"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list users — skipping cleanup")
        return
    for u in data.get("Data", []):
        if (u.get("Email") or u.get("email") or "").lower() == MARKER_EMAIL:
            uid = u.get("Id") or u.get("id")
            if uid:
                logger.info("Deleting lifecycle user id=%s", uid)
                run_cli(["admin", "users", "delete", uid])


main()
sys.exit(0)
