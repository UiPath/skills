#!/usr/bin/env python3
"""Best-effort cleanup: revoke leaked/test PATs so the create/revoke smokes have
a free slot (the tenant caps a user at 5 PATs).

Revokes any PAT whose description matches a known TEST marker (case-insensitive
substring): the identity smoke marker plus historical leaks left by the older
cleanup_pat.py, which keyed on lowercase 'description' and matched nothing.
Only test-created PATs are targeted — real/operational PATs are left intact.

Always exits 0 — failures here never affect pass/fail. Uses the PascalCase
Description/Id keys the tenant actually returns.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_pat_marker: %(message)s")
logger = logging.getLogger(__name__)

# Case-insensitive substrings that identify a test-created PAT. Deliberately
# distinctive — a bare "smoke" would also revoke real PATs (e.g. a production
# "smoke-test detector" token) on the shared org.
TEST_MARKERS = ("ce-identity-smoke", "e2e-test-pat")


def is_test_pat(desc):
    d = (desc or "").lower()
    return any(m in d for m in TEST_MARKERS)


def main():
    data = run_cli(["admin", "pat", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list PATs — skipping cleanup")
        return

    for t in data.get("Data", []):
        desc = t.get("Description") or t.get("description") or ""
        if is_test_pat(desc):
            token_id = t.get("Id") or t.get("id")
            if not token_id:
                continue
            logger.info("Revoking test PAT (description=%r, id=%s)", desc, token_id)
            result = run_cli(["admin", "pat", "revoke", token_id])
            if result:
                logger.info("Revoke result: %s", result.get("Result"))


main()
sys.exit(0)
