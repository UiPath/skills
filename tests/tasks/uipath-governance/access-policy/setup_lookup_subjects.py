#!/usr/bin/env python3
"""Pre-run seed: real directory subjects for the identity-lookup scenario.

  GOV_GROUP_BASE  base name for a marker directory group (optional)
  GOV_ROBOT_BASE  base name for a marker robot account (optional)

Both names get this run's id appended and are recorded in seed.json under
"subjects", so the check and the cleanup read the names this run actually
created rather than a shared constant. Two agents running this task at the same
time therefore create, resolve and remove different subjects.

Idempotent: an existing subject with the same name is reused. Always exits 0.
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
from gov_helpers import run_cli, run_id, scoped, update_seed

logging.basicConfig(level=logging.INFO, format="setup_lookup_subjects: %(message)s")
logger = logging.getLogger(__name__)


def find(kind: str, name: str) -> dict | None:
    data = run_cli(["admin", kind, "list"])
    if not data or data.get("Result") != "Success":
        return None
    for row in (data.get("Data") or []):
        if (row.get("Name") or row.get("name") or "") == name:
            return row
    return None


def ensure(kind: str, name: str) -> dict | None:
    existing = find(kind, name)
    if existing:
        return existing
    res = run_cli(["admin", kind, "create", name])
    if not res or res.get("Result") != "Success":
        logger.warning("Could not create %s '%s': %s", kind, name, res)
        return None
    return find(kind, name)


def main():
    group_base = (os.environ.get("GOV_GROUP_BASE") or "").strip()
    robot_base = (os.environ.get("GOV_ROBOT_BASE") or "").strip()
    subjects = {}

    if group_base:
        name = scoped(group_base)
        group = ensure("groups", name)
        if group:
            subjects["groupName"] = name
            subjects["groupId"] = group.get("Id") or group.get("id")

    if robot_base:
        name = scoped(robot_base)
        robot = ensure("robot-accounts", name)
        if robot:
            subjects["robotName"] = name
            subjects["robotId"] = robot.get("Id") or robot.get("id")

    if subjects:
        update_seed(subjects=subjects)
        logger.info("Run %s seeded %s", run_id(), subjects)


main()
sys.exit(0)
