#!/usr/bin/env python3
"""Best-effort cleanup: delete all 'john.doe@example.com' users.

Always exits 0 — failures here never affect pass/fail.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_shared'))
from admin_helpers import run_cli, find_all

logging.basicConfig(level=logging.INFO, format="cleanup_user: %(message)s")
logger = logging.getLogger(__name__)


def main():
    data = run_cli(["admin", "users", "list", "--search", "john.doe@example.com"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list users — skipping cleanup")
        return

    matches = find_all(data, "john.doe@example.com", ["email", "userName"])
    if not matches:
        logger.info("No 'john.doe@example.com' user found — nothing to clean up")
        return

    for u in matches:
        user_id = u.get("id")
        if not user_id:
            continue
        logger.info("Deleting user (id=%s)", user_id)
        result = run_cli(["admin", "users", "delete", user_id])
        if result:
            logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
        else:
            logger.warning("Delete call returned no result for id=%s", user_id)


if __name__ == "__main__":
    main()
    sys.exit(0)
