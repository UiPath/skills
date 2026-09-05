#!/usr/bin/env python3
"""Post-run cleanup for the identity-lookup subjects — this run's only.

Names are read from seed.json, so a concurrently executing run's group and robot
account (which carry a different run id) are never removed. Always exits 0.
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
from gov_helpers import load_seed, owned_by_this_run, run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_lookup_subjects: %(message)s")
logger = logging.getLogger(__name__)


def main():
    subjects = (load_seed().get("subjects") or {})
    for kind, name_key, id_key in (("groups", "groupName", "groupId"),
                                   ("robot-accounts", "robotName", "robotId")):
        name, oid = subjects.get(name_key), subjects.get(id_key)
        if not name or not oid:
            continue
        if not owned_by_this_run(name):
            logger.info("Skipping '%s' — not owned by this run", name)
            continue
        logger.info("Deleting %s '%s' (%s)", kind, name, oid)
        run_cli(["admin", kind, "delete", oid])


main()
sys.exit(0)
