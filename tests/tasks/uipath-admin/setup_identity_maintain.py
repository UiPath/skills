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

The stale group gets a DEDICATED marker user as its member (invited here, removed
by cleanup) so the agent has a real member record to inspect before retiring the
group. It deliberately does NOT use "the first user in the org": that pulled a
real employee's account into the fixture and wrote their email address into
downloadable CI artifacts.

Also records the org's pre-existing custom groups so verify can assert the agent
deleted only its own fixtures. Always exits 0.
"""

import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll

logging.basicConfig(level=logging.INFO, format="setup_identity_maintain: %(message)s")
logger = logging.getLogger(__name__)

GROUP_RENAME = "ce-identity-maintain-group"
GROUP_RENAMED = "ce-identity-maintain-group-renamed"
GROUP_STALE = "ce-identity-maintain-stale-group"
BOT_UPDATE = "ce-identity-maintain-bot"
BOT_RETIRE = "ce-identity-maintain-retired-bot"

# Dedicated fixture member — never a real employee.
MEMBER_EMAIL = "ce-identity-maintain-member@example.com"
MEMBER_SEARCH = "ce-identity-maintain-member"

# Includes the post-rename name so a re-run starts from a clean slate.
ALL_GROUPS = (GROUP_RENAME, GROUP_RENAMED, GROUP_STALE)
ALL_BOTS = (BOT_UPDATE, BOT_RETIRE)

# Snapshot of non-fixture groups, so verify can prove no collateral deletion.
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_identity_maintain_seed.json")


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


def find_member():
    """Resolve the dedicated fixture member user, if it exists."""
    data = run_cli(["admin", "users", "list", "--search", MEMBER_SEARCH])
    if not data or data.get("Result") != "Success":
        return None
    for u in data.get("Data", []):
        if (u.get("Email") or u.get("email") or "").lower() == MEMBER_EMAIL:
            return u
    return None


def member_user_id():
    """Invite (idempotently) and return the dedicated fixture member's id.

    Never selects a real org user: pulling "the first user in the org" into the
    fixture leaked a named employee's email into CI artifacts.
    """
    existing = find_member()
    if existing and _id(existing):
        return _id(existing)
    res = run_cli(["admin", "users", "invite", "--email", MEMBER_EMAIL,
                   "--name", "Maintain", "--surname", "FixtureMember"])
    if not res or res.get("Result") != "Success":
        logger.warning("Could not invite fixture member '%s': %s", MEMBER_EMAIL, res)
        return None
    u = poll(find_member)
    return _id(u) if u else None


def snapshot_other_groups():
    """Record every group that is NOT one of this test's fixtures.

    verify asserts all of these still exist, so an agent that over-deletes on the
    shared org fails instead of passing because its own fixtures happen to be in
    the expected state.
    """
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not snapshot pre-existing groups — collateral check will be skipped")
        return
    others = sorted(
        _name(g) for g in data.get("Data", [])
        if _name(g) and _name(g) not in ALL_GROUPS
    )
    with open(STATE_FILE, "w") as f:
        json.dump({"other_groups": others}, f)
    logger.info("Snapshotted %d non-fixture groups for the collateral-deletion check", len(others))


def group_id(name):
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for g in data.get("Data", []):
        if _name(g) == name:
            return _id(g)
    return None


def main():
    try:
        os.remove(STATE_FILE)
    except OSError:
        pass

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

    # Give the stale group the dedicated fixture member so the agent has an
    # account record to inspect before retiring it. Best-effort only.
    uid = member_user_id()
    gid = group_id(GROUP_STALE)
    if uid and gid:
        res = run_cli(["admin", "groups", "members", "add", gid, "--user-ids", uid])
        logger.info("Seeded fixture member on '%s': %s", GROUP_STALE, (res or {}).get("Result"))
    else:
        logger.warning("Could not seed a member on '%s' (uid=%s gid=%s)", GROUP_STALE, uid, gid)

    # Snapshot last, so the fixtures themselves are excluded by name.
    snapshot_other_groups()


main()
sys.exit(0)
