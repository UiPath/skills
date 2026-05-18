#!/usr/bin/env python3
"""Best-effort cleanup: delete the 'smoke-e2e-bot' robot account created by e2e tests.

Always exits 0 — failures here never affect pass/fail.
"""

import json
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_robot: %(message)s")
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
    data = run_cli(["admin", "robot-accounts", "list", "--search", "smoke-e2e-bot"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list robot accounts — skipping cleanup")
        return

    for r in data.get("Data", []):
        if "smoke-e2e-bot" in (r.get("name") or ""):
            robot_id = r.get("id")
            logger.info("Deleting robot account '%s' (id=%s)", r.get("name"), robot_id)
            run_cli(["admin", "robot-accounts", "delete", robot_id])
            return

    logger.info("Robot account 'smoke-e2e-bot' not found — nothing to clean up")


if __name__ == "__main__":
    main()
    sys.exit(0)
