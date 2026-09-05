#!/usr/bin/env python3
"""Best-effort cleanup: delete SMTP settings (revert to platform defaults).

Always exits 0 — failures here never affect pass/fail.
"""

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

logging.basicConfig(level=logging.INFO, format="cleanup_smtp: %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Deleting SMTP settings (revert to defaults)")
    result = run_cli(["admin", "smtp", "delete"])
    if result:
        logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
    else:
        logger.warning("Delete call returned no result")


main()
sys.exit(0)
