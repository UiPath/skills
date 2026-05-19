#!/usr/bin/env python3
"""Best-effort cleanup: revoke all PATs with description 'e2e-test-pat'.

Always exits 0 — failures here never affect pass/fail.
"""

import logging
import sys

sys.path.insert(0, sys.path[0])
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_pat: %(message)s")
logger = logging.getLogger(__name__)


def main():
    data = run_cli(["admin", "pat", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list PATs — skipping cleanup")
        return

    for t in data.get("Data", []):
        if (t.get("description") or "") == "e2e-test-pat":
            token_id = t.get("id")
            if not token_id:
                continue
            logger.info("Revoking PAT (id=%s)", token_id)
            result = run_cli(["admin", "pat", "revoke", token_id])
            if result:
                logger.info("Revoke result: %s — %s", result.get("Result"), result.get("Message", ""))
            else:
                logger.warning("Revoke call returned no result for id=%s", token_id)


if __name__ == "__main__":
    main()
    sys.exit(0)
