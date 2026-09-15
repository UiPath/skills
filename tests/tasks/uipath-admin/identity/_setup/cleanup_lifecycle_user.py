#!/usr/bin/env python3
"""Best-effort cleanup: delete the lifecycle-smoke user by marker email."""

import logging
import sys

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
