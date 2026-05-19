#!/usr/bin/env python3
"""Best-effort cleanup: delete SMTP settings (revert to platform defaults).

Always exits 0 — failures here never affect pass/fail.
"""

import logging
import sys

sys.path.insert(0, sys.path[0])
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


if __name__ == "__main__":
    main()
    sys.exit(0)
