#!/usr/bin/env python3
"""Best-effort cleanup: delete the 'Invoice Processing Team' group created by e2e tests.

Always exits 0 — failures here never affect pass/fail.
"""

import json
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_group: %(message)s")
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
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list groups — skipping cleanup")
        return

    for g in data.get("Data", []):
        name = g.get("name") or g.get("displayName") or ""
        if "Invoice Processing Team" in name:
            group_id = g.get("id")
            logger.info("Deleting group '%s' (id=%s)", name, group_id)
            run_cli(["admin", "groups", "delete", group_id])
            return

    logger.info("Group 'Invoice Processing Team' not found — nothing to clean up")


if __name__ == "__main__":
    main()
    sys.exit(0)
