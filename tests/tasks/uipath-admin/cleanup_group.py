#!/usr/bin/env python3
"""Best-effort cleanup: delete all 'Invoice Processing Team' groups.

Always exits 0 — failures here never affect pass/fail.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shared"))
from admin_helpers import run_cli, find_all

logging.basicConfig(level=logging.INFO, format="cleanup_group: %(message)s")
logger = logging.getLogger(__name__)


def main():
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list groups — skipping cleanup")
        return

    matches = find_all(data, "Invoice Processing Team", ["name", "displayName"])
    if not matches:
        logger.info("No 'Invoice Processing Team' group found — nothing to clean up")
        return

    for g in matches:
        group_id = g.get("id")
        if not group_id:
            continue
        logger.info("Deleting group (id=%s)", group_id)
        result = run_cli(["admin", "groups", "delete", group_id])
        if result:
            logger.info(
                "Delete result: %s — %s",
                result.get("Result"),
                result.get("Message", ""),
            )
        else:
            logger.warning("Delete call returned no result for id=%s", group_id)


main()
sys.exit(0)
