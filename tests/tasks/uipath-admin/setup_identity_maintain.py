#!/usr/bin/env python3
"""Pre-run seed for the identity-maintain e2e: (re)create the four marker objects
the agent must inspect, modify, and retire.

Seeds two custom groups and two robot accounts so the run can grade an UPDATE
and a DELETE on each object type without the delete erasing the update evidence
(see identity_user_lifecycle_e2e.yaml for that constraint):

  ce-identity-maintain-group        -> agent renames it
  ce-identity-maintain-stale-group  -> agent deletes it (seeded with one member)
  ce-identity-maintain-bot          -> agent updates its display name
  ce-identity-maintain-retired-bot  -> agent deletes it

The stale group gets the first org user as a member so the agent has a real
member record to inspect before retiring the group. Best-effort: a tenant with
no listable users simply yields an empty group. Always exits 0.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="setup_identity_maintain: %(message)s")
logger = logging.getLogger(__name__)

GROUP_RENAME = "ce-identity-maintain-group"
GROUP_RENAMED = "ce-identity-maintain-group-renamed"
GROUP_STALE = "ce-identity-maintain-stale-group"
BOT_UPDATE = "ce-identity-maintain-bot"
BOT_RETIRE = "ce-identity-maintain-retired-bot"

# Includes the post-rename name so a re-run starts from a clean slate.
ALL_GROUPS = (GROUP_RENAME, GROUP_RENAMED, GROUP_STALE)
ALL_BOTS = (BOT_UPDATE, BOT_RETIRE)


def _id(item):
    return item.get("Id") or item.get("id")


def _name(item):
    return item.get("Name") or item.get("name") or item.get("displayName") or ""


def drop_groups():
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return
    for g in data.get("Data", []):
        if _name(g) in ALL_GROUPS and _id(g):
            run_cli(["admin", "groups", "delete", _id(g)])


def drop_bots():
    data = run_cli(["admin", "robot-accounts", "list", "--search", "ce-identity-maintain"])
    if not data or data.get("Result") != "Success":
        return
    for r in data.get("Data", []):
        if _name(r) in ALL_BOTS and _id(r):
            run_cli(["admin", "robot-accounts", "delete", _id(r)])


def first_user_id():
    data = run_cli(["admin", "users", "list", "--limit", "1"])
    if not data or data.get("Result") != "Success":
        return None
    for u in data.get("Data", []):
        if _id(u):
            return _id(u)
    return None


def group_id(name):
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for g in data.get("Data", []):
        if _name(g) == name:
            return _id(g)
    return None


def main():
    drop_groups()
    drop_bots()

    for name in (GROUP_RENAME, GROUP_STALE):
        res = run_cli(["admin", "groups", "create", name])
        logger.info("Seeded group '%s': %s", name, (res or {}).get("Result"))

    res = run_cli(["admin", "robot-accounts", "create", BOT_UPDATE,
                   "--display-name", "Maintain Bot"])
    logger.info("Seeded robot '%s': %s", BOT_UPDATE, (res or {}).get("Result"))
    res = run_cli(["admin", "robot-accounts", "create", BOT_RETIRE,
                   "--display-name", "Retired Bot"])
    logger.info("Seeded robot '%s': %s", BOT_RETIRE, (res or {}).get("Result"))

    # Give the stale group one real member so the agent has an account record to
    # inspect before retiring it. Best-effort only.
    uid = first_user_id()
    gid = group_id(GROUP_STALE)
    if uid and gid:
        res = run_cli(["admin", "groups", "members", "add", gid, "--user-ids", uid])
        logger.info("Seeded member on '%s': %s", GROUP_STALE, (res or {}).get("Result"))
    else:
        logger.warning("Could not seed a member on '%s' (uid=%s gid=%s)", GROUP_STALE, uid, gid)


main()
sys.exit(0)
