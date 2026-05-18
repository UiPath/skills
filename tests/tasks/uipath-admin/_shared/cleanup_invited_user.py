#!/usr/bin/env python3
"""Best-effort cleanup: delete the 'john.doe@example.com' user created by e2e tests.

Always exits 0 — failures here never affect pass/fail.
"""

import json
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_user: %(message)s")
logger = logging.getLogger(__name__)


def run_cli(args: list[str]) -> dict | None:
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=30,
        )
        return json.loads(result.stdout)
    except Exception as e:
        logger.warning("CLI call failed: %s", e)
        return None


def main():
    data = run_cli(["admin", "users", "list", "--search", "john.doe@example.com"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list users — skipping cleanup")
        return

    for u in data.get("Data", []):
        email = u.get("email") or u.get("userName") or ""
        if "john.doe@example.com" in email:
            user_id = u.get("id")
            logger.info("Deleting user '%s' (id=%s)", email, user_id)
            run_cli(["admin", "users", "delete", user_id])
            return

    logger.info("User 'john.doe@example.com' not found — nothing to clean up")


if __name__ == "__main__":
    main()
    sys.exit(0)
