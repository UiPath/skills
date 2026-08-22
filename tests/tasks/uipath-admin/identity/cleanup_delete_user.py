#!/usr/bin/env python3
"""Best-effort cleanup: delete the delete-smoke marker user if the agent left it
behind (e.g. it never ran the delete), so the test does not leak users onto the
org. Also clears the seed state file. Idempotent; always exits 0."""

import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_delete_user: %(message)s")
logger = logging.getLogger(__name__)

MARKER_EMAIL = "ce-identity-delete@example.com"
SEARCH = "ce-identity-delete"
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_delete_user_seed.txt")


def main():
    data = run_cli(["admin", "users", "list", "--search", SEARCH])
    if data and data.get("Result") == "Success":
        for u in data.get("Data", []):
            if (u.get("Email") or u.get("email") or "").lower() == MARKER_EMAIL:
                uid = u.get("Id") or u.get("id")
                if uid:
                    logger.info("Deleting leftover delete-smoke user id=%s", uid)
                    run_cli(["admin", "users", "delete", uid])
    else:
        logger.warning("Could not list users — skipping cleanup")

    try:
        os.remove(STATE_FILE)
    except OSError:
        pass


main()
sys.exit(0)
