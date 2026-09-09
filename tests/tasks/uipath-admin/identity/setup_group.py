#!/usr/bin/env python3
"""Pre-run seed for the group-membership smoke: (re)create the marker group so the
agent has an existing group to add a member to. Always exits 0."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="setup_group: %(message)s")
logger = logging.getLogger(__name__)

GROUP = "ce-identity-smoke-group"


def main():
    # Remove any leftover marker group first (idempotent seed).
    data = run_cli(["admin", "groups", "list"])
    if data and data.get("Result") == "Success":
        for g in data.get("Data", []):
            if (g.get("Name") or g.get("name") or "") == GROUP:
                gid = g.get("Id") or g.get("id")
                if gid:
                    run_cli(["admin", "groups", "delete", gid])

    res = run_cli(["admin", "groups", "create", GROUP])
    logger.info("Seeded group '%s': %s", GROUP, (res or {}).get("Result"))


main()
sys.exit(0)
