#!/usr/bin/env python3
"""Best-effort cleanup: revoke all PATs with the smoke marker description.

Always exits 0 — failures here never affect pass/fail. Uses the PascalCase
Description/Id keys the tenant actually returns (the older cleanup_pat.py keyed
on lowercase 'description' and silently matched nothing).
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_pat_marker: %(message)s")
logger = logging.getLogger(__name__)

MARKER = "ce-identity-smoke-pat"


def main():
    data = run_cli(["admin", "pat", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list PATs — skipping cleanup")
        return

    for t in data.get("Data", []):
        desc = t.get("Description") or t.get("description") or ""
        if desc == MARKER:
            token_id = t.get("Id") or t.get("id")
            if not token_id:
                continue
            logger.info("Revoking PAT id=%s", token_id)
            result = run_cli(["admin", "pat", "revoke", token_id])
            if result:
                logger.info("Revoke result: %s", result.get("Result"))


main()
sys.exit(0)
