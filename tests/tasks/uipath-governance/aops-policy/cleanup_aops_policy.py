#!/usr/bin/env python3
"""Post-run cleanup for the aops-policy suite — this run's policies only.

The run id is a substring of every name this run created, so a server-side
`list --search <run id>` finds exactly this run's policies and nothing from a
concurrently executing one. Identifiers recorded in seed.json are also removed,
which covers a policy the agent renamed.

Deleting a policy renumbers the product's remaining priorities, which is why no
check in this suite asserts another policy's priority.

Always exits 0 — cleanup never decides pass/fail.
"""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-governance", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from gov_helpers import aops_delete, aops_search, load_seed, owned_by_this_run, poll

logging.basicConfig(level=logging.INFO, format="cleanup_aops_policy: %(message)s")
logger = logging.getLogger(__name__)


def main():
    seed = load_seed()
    token = seed.get("uuid8")
    if not token:
        logger.info("No seed.json in the run directory — nothing owned by this run")
        return

    removed = set()
    # The search read is retried: one failed read would otherwise leak every
    # policy this run created.
    for row in (poll(lambda: aops_search(token), max_attempts=3, delay=5) or []):
        name = row.get("Name") or ""
        ident = row.get("Identifier")
        if ident and owned_by_this_run(name) and aops_delete(ident):
            removed.add(ident)
            logger.info("Deleted '%s' (%s)", name, ident)

    for key, entry in seed.items():
        if isinstance(entry, dict) and entry.get("identifier") and entry["identifier"] not in removed:
            if aops_delete(entry["identifier"]):
                removed.add(entry["identifier"])
                logger.info("Deleted policy recorded under seed key '%s' (%s)", key, entry["identifier"])

    logger.info("Run %s: removed %d policy/policies", token, len(removed))


main()
sys.exit(0)
