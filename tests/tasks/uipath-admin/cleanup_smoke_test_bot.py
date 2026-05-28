#!/usr/bin/env python3
"""Best-effort cleanup: delete all 'smoke-test-bot' robot accounts.

Always exits 0 — failures here never affect pass/fail.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, find_all

logging.basicConfig(level=logging.INFO, format="cleanup_smoke_test_bot: %(message)s")
logger = logging.getLogger(__name__)


def main():
    data = run_cli(["admin", "robot-accounts", "list", "--search", "smoke-test-bot"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list robot accounts — skipping cleanup")
        return

    matches = find_all(data, "smoke-test-bot", ["name"])
    if not matches:
        logger.info("No 'smoke-test-bot' robot account found — nothing to clean up")
        return

    for r in matches:
        robot_id = r.get("id")
        if not robot_id:
            continue
        logger.info("Deleting robot account (id=%s)", robot_id)
        result = run_cli(["admin", "robot-accounts", "delete", robot_id])
        if result:
            logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
        else:
            logger.warning("Delete call returned no result for id=%s", robot_id)


main()
sys.exit(0)
