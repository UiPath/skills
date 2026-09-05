#!/usr/bin/env python3
"""Best-effort cleanup for IP-restriction tests: delete marker allowlist entries.

  APMS_CLEANUP_MARKER  substring identifying test-owned entries, e.g. `ce-apms-`.
                       An entry is removed only when its name ALSO carries this
                       run's uuid8 (from seed.json).

CONCURRENCY: several agents run these tasks against one organization at once, and
allowlist entries are keyed by CIDR, so a marker-only sweep would delete a peer
run's in-flight block. Restricting removal to this run's own suffix keeps runs
from cleaning up after each other. A real office range is never touched, and
enforcement is never toggled by these tests, so removal cannot lock anyone out.

Always exits 0 — cleanup failures never affect pass/fail.
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
from admin_helpers import owned_by_this_run, run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_apms_marker: %(message)s")
logger = logging.getLogger(__name__)


def main():
    marker = (os.environ.get("APMS_CLEANUP_MARKER") or "").strip()
    if not marker:
        logger.warning("APMS_CLEANUP_MARKER not set — nothing to do")
        return

    data = run_cli(["admin", "ip-restriction", "ip-ranges", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list IP ranges — skipping cleanup")
        return

    for entry in (data.get("Data") or []):
        name = entry.get("Name") or ""
        entry_id = entry.get("Id")
        if marker in name and owned_by_this_run(name) and entry_id:
            logger.info("Deleting allowlist entry '%s' (id=%s)", name, entry_id)
            run_cli(["admin", "ip-restriction", "ip-ranges", "delete", entry_id, "--confirm"])


main()
sys.exit(0)
