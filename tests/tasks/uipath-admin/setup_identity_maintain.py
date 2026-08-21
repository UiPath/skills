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

Also records the seeded object ids and the org's pre-existing custom groups, so
verify can assert its own preconditions, prove deletion by ID (a rename preserves
the id, so name-absence alone cannot distinguish delete from rename), and detect
collateral deletion.

EXITS NON-ZERO on any required-fixture failure.
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


def die(message):
    """Exit non-zero so coder_eval flags the run.

    An earlier revision always exited 0, so a silently failed `create` left the
    corresponding assertion to pass vacuously with a success line identical to a
    real pass. coder_eval treats a failing pre_run as a run ERROR.
    """
    logger.error("SEED FAILED: %s", message)
    sys.exit(1)

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
# Groups created by any admin test share this prefix and are excluded — see
# snapshot_other_groups().
FIXTURE_PREFIX = "ce-"

# Groups created and destroyed by OTHER admin tasks that do NOT use the fixture
# prefix. group_membership_management_e2e creates "Invoice Processing Team" and
# instructs the agent to delete it first, so snapshotting that name made a
# sibling's normal operation fail this task under -j4. Round 4 fixed the
# ce-prefixed instance of this and missed the unprefixed one.
SIBLING_FIXTURE_GROUPS = ("Invoice Processing Team",)
LIST_LIMIT = "200"
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_identity_maintain_seed.json")


def _id(item):
    return item.get("Id") or item.get("id")


def _name(item):
    return item.get("Name") or item.get("name") or item.get("displayName") or ""


# `groups list` reports Type as a numeric enum: 0 = built-in, 1 = custom. The
# skill docs say `type: "BuiltIn"`, a value that never appears in CLI output.
BUILTIN_GROUP_TYPE = 0


def _is_builtin(group):
    raw = group.get("Type", group.get("type"))
    if isinstance(raw, bool):
        return False
    if isinstance(raw, int):
        return raw == BUILTIN_GROUP_TYPE
    if isinstance(raw, str):
        text = raw.strip()
        return text == str(BUILTIN_GROUP_TYPE) or text.lower() in {"builtin", "built-in", "system"}
    return False


def drop_groups():
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return
    for g in data.get("Data", []):
        if _name(g) in ALL_GROUPS and _id(g):
            run_cli(["admin", "groups", "delete", _id(g)])


def drop_bots():
    data = run_cli(["admin", "robot-accounts", "list", "--search", "ce-identity-maintain", "--limit", LIST_LIMIT])
    if not data or data.get("Result") != "Success":
        return
    for r in data.get("Data", []):
        if _name(r) in ALL_BOTS and _id(r):
            run_cli(["admin", "robot-accounts", "delete", _id(r)])


def find_member():
    """Resolve the dedicated fixture member user, if it exists."""
    data = run_cli(["admin", "users", "list", "--search", MEMBER_SEARCH, "--limit", LIST_LIMIT])
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
    """Return every group that is NOT one of this test's fixtures.

    verify asserts all of these still exist, so an agent that over-deletes on the
    shared org fails instead of passing because its own fixtures happen to be in
    the expected state. Dies rather than returning empty: an empty snapshot makes
    the collateral check vacuous, and a shared org always has built-in groups.
    """
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        die("could not snapshot pre-existing groups — the collateral-deletion check "
            "would be vacuous without a baseline")
    # Exclude every test-fixture group, not just this task's. Sibling admin tasks
    # create and tear down their own `ce-*` groups (e.g. setup_group.py creates
    # ce-identity-smoke-group, cleanup_group_marker.py deletes it), and the nightly
    # runs with TASK_PARALLELISM. Snapshotting those names meant a sibling's
    # teardown mid-run produced
    #   "FAIL: 1 non-fixture group(s) were deleted: ['ce-identity-smoke-group']"
    # blaming the agent for another task's cleanup. Real shared groups
    # (FinanceAdmins, Data Team, Compliance, built-ins) do not use the prefix, so
    # they are still protected.
    rows = [g for g in data.get("Data", []) if _name(g)]
    # Built-in groups are never legitimately deleted by any test, so they are
    # asserted strictly. Custom groups can belong to a concurrent sibling, so
    # known sibling fixtures and anything prefixed are excluded.
    builtins = sorted(_name(g) for g in rows if _is_builtin(g))
    others = sorted(
        _name(g) for g in rows
        if not _is_builtin(g)
        and _name(g) not in ALL_GROUPS
        and _name(g) not in SIBLING_FIXTURE_GROUPS
        and not _name(g).startswith(FIXTURE_PREFIX)
    )
    if not builtins:
        die("snapshot found no built-in groups — a shared org always has them, so this "
            "means the listing was truncated or the Type field changed shape")
    return builtins, others


def robot_id(name):
    data = run_cli(["admin", "robot-accounts", "list", "--search", "ce-identity-maintain",
                    "--limit", LIST_LIMIT])
    if not data or data.get("Result") != "Success":
        return None
    for r in data.get("Data", []):
        if _name(r) == name:
            return _id(r)
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
    try:
        os.remove(STATE_FILE)
    except OSError:
        pass

    drop_groups()
    drop_bots()

    for name in (GROUP_RENAME, GROUP_STALE):
        res = run_cli(["admin", "groups", "create", name])
        if not res or res.get("Result") != "Success":
            die(f"could not create group '{name}': {res}")
        logger.info("Seeded group '%s'", name)

    for bot, display in ((BOT_UPDATE, "Maintain Bot"), (BOT_RETIRE, "Retired Bot")):
        res = run_cli(["admin", "robot-accounts", "create", bot, "--display-name", display])
        if not res or res.get("Result") != "Success":
            die(f"could not create robot account '{bot}': {res}")
        logger.info("Seeded robot '%s'", bot)

    # Resolve the seeded ids. Deletion is later proved by ID absence, so these are
    # required, not best-effort.
    ids = {}
    for name in (GROUP_RENAME, GROUP_STALE):
        gid = poll(lambda n=name: group_id(n))
        if not gid:
            die(f"group '{name}' not resolvable after create")
        ids[name] = str(gid)
    for bot in ALL_BOTS:
        rid = poll(lambda b=bot: robot_id(b))
        if not rid:
            die(f"robot account '{bot}' not resolvable after create")
        ids[bot] = str(rid)

    # Give the stale group the dedicated fixture member so the agent has an
    # account record to inspect before retiring it.
    uid = member_user_id()
    if not uid:
        die(f"could not seed the fixture member '{MEMBER_EMAIL}' — the prompt asks the "
            "agent to report who is in the stale group")
    res = run_cli(["admin", "groups", "members", "add", ids[GROUP_STALE], "--user-ids", uid])
    if not res or res.get("Result") != "Success":
        die(f"could not add the fixture member to '{GROUP_STALE}': {res}")
    logger.info("Seeded fixture member on '%s'", GROUP_STALE)

    # Snapshot last, so the fixtures themselves are excluded by name.
    builtins, others = snapshot_other_groups()

    with open(STATE_FILE, "w") as f:
        json.dump({
            "builtin_groups": builtins,
            "other_groups": others,
            "group_rename_id": ids[GROUP_RENAME],
            "group_stale_id": ids[GROUP_STALE],
            "bot_update_id": ids[BOT_UPDATE],
            "bot_retire_id": ids[BOT_RETIRE],
            "member_user_id": str(uid),
        }, f)
    logger.info("Recorded seed state: %d built-in + %d other non-fixture groups, 4 fixture ids",
                len(builtins), len(others))


main()
