#!/usr/bin/env python3
"""Best-effort cleanup: delete groups whose name contains the smoke marker."""

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

logging.basicConfig(level=logging.INFO, format="cleanup_group_marker: %(message)s")
logger = logging.getLogger(__name__)

MARKER = "ce-identity-smoke-group"


def main():
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list groups — skipping cleanup")
        return
    for g in data.get("Data", []):
        name = g.get("Name") or g.get("name") or ""
        if MARKER in name:
            gid = g.get("Id") or g.get("id")
            if gid:
                logger.info("Deleting group id=%s", gid)
                run_cli(["admin", "groups", "delete", gid])


main()
sys.exit(0)
