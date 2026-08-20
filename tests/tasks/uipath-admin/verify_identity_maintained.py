#!/usr/bin/env python3
"""Verify the identity-maintain e2e outcome by reading tenant state back.

Assertions, all outcome-graded (never a command string) and all checked against
the seed baseline in the state file:

  1. groups update  — the SEEDED group id now carries the renamed name, and the
                      old name is gone. Comparing ids is what proves an in-place
                      rename rather than a create-a-new-group shortcut.
  2. groups delete  — the seeded stale group's ID is absent. Name-absence alone
                      would accept an archive-instead-of-delete, since a rename
                      preserves the id.
  3. robot update   — the seeded robot id still exists and its display name is
                      now 'Maintain Bot Updated' (seeded as 'Maintain Bot').
  4. robot delete   — the seeded retired robot's ID cannot be fetched. Proved
                      by a direct `robot-accounts get <ID>`, not by absence
                      from a name-filtered list (a rename would hide it).
  5. no collateral  — every non-fixture group present at seed time still exists.
                      This is also what protects built-in groups: they are in
                      the snapshot and never carry the fixture prefix. There is
                      deliberately NO separate built-in assertion — it would add
                      no coverage and could false-fail on a Type field rename.

Any missing or degenerate seed baseline is a hard failure, not a skipped check:
an absent state file and a valid-but-empty snapshot both used to pass silently,
which is the vacuous-pass shape this suite exists to avoid.
"""

import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_identity_maintained: %(message)s")

GROUP_SEEDED = "ce-identity-maintain-group"
GROUP_RENAMED = "ce-identity-maintain-group-renamed"
GROUP_STALE = "ce-identity-maintain-stale-group"
BOT_KEPT = "ce-identity-maintain-bot"
BOT_RETIRED = "ce-identity-maintain-retired-bot"
EXPECTED_DISPLAY_NAME = "Maintain Bot Updated"
LIST_LIMIT = "200"
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_identity_maintain_seed.json")

SEED_KEYS = ("other_groups", "group_rename_id", "group_stale_id",
             "bot_update_id", "bot_retire_id")


def _name(item):
    return item.get("Name") or item.get("name") or item.get("displayName") or ""


def _id_of(item):
    if not item:
        return None
    return item.get("Id") or item.get("id")


# `groups list` reports Type as a numeric enum, NOT the string the skill docs
# imply: 0 = built-in (Everyone, Administrators, Automation Users, ...),
# 1 = custom. SKILL.md anti-pattern 1 describes these as `type: "BuiltIn"`,
# which never appears in CLI output — comparing against that string silently
# matched nothing and reported every tenant as having no built-ins left.
# Reported for information only; the collateral check below is what actually
# protects built-ins, since they are all present in the seed snapshot.
BUILTIN_GROUP_TYPE = 0


def _is_builtin(group):
    raw = group.get("Type", group.get("type"))
    if isinstance(raw, bool):
        return False
    if isinstance(raw, int):
        return raw == BUILTIN_GROUP_TYPE
    if isinstance(raw, str):
        text = raw.strip()
        # Tolerate a future CLI that switches the enum to a label or numeric string.
        return text == str(BUILTIN_GROUP_TYPE) or text.lower() in {"builtin", "built-in", "system"}
    return False


def groups():
    # `groups list` documents no pagination flags and rejects --limit
    # (ValidationError/invalid_argument); it returns the full set.
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data", [])


def robots():
    data = run_cli(["admin", "robot-accounts", "list", "--search", "ce-identity-maintain",
                    "--limit", LIST_LIMIT])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data", [])


def load_seed():
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError) as exc:
        fail(f"seed state file {STATE_FILE} missing or malformed ({exc}) — cannot verify "
             "preconditions; setup_identity_maintain.py did not complete")
    for key in SEED_KEYS:
        if not state.get(key):
            fail(f"seed state is missing or empty for '{key}' — setup did not record a complete "
                 "baseline, so the corresponding assertion would be vacuous")
    return state


def main():
    seed = load_seed()
    expected_others = seed["other_groups"]
    rename_id = str(seed["group_rename_id"])
    stale_id = str(seed["group_stale_id"])
    bot_update_id = str(seed["bot_update_id"])
    bot_retire_id = str(seed["bot_retire_id"])

    # Poll for the renamed group so eventual consistency does not fail the run.
    def renamed_present():
        gs = groups()
        if gs is None:
            return None
        return gs if any(_name(g) == GROUP_RENAMED for g in gs) else None

    gs = poll(renamed_present)
    if gs is None:
        gs = groups()
        if gs is None:
            fail("could not list groups — cannot verify tenant state")
        names = sorted(_name(g) for g in gs if _name(g).startswith("ce-identity-maintain"))
        fail(f"group '{GROUP_RENAMED}' not found — rename did not land; markers present: {names}")

    group_names = [_name(g) for g in gs]
    group_ids = {str(_id_of(g)) for g in gs if _id_of(g)}

    if GROUP_SEEDED in group_names:
        fail(f"group still named '{GROUP_SEEDED}' — a new group was created instead of renaming "
             "the existing one")

    renamed = next((g for g in gs if _name(g) == GROUP_RENAMED), None)
    if str(_id_of(renamed)) != rename_id:
        fail(f"'{GROUP_RENAMED}' has id={_id_of(renamed)} but the seeded group was {rename_id} — a "
             "new group was created instead of renaming the existing one in place")

    if stale_id in group_ids:
        surviving = next((_name(g) for g in gs if str(_id_of(g)) == stale_id), "?")
        fail(f"the stale group (id={stale_id}) still exists as '{surviving}' — it was renamed or "
             "left in place, not deleted")

    gone = sorted(set(expected_others) - set(group_names))
    if gone:
        fail(f"{len(gone)} non-fixture group(s) were deleted: {gone[:12]} — the agent must only "
             "touch the objects it was asked about")

    def bot_updated():
        rs = robots()
        if rs is None:
            return None
        for r in rs:
            if _name(r) == BOT_KEPT:
                return r
        return None

    bot = poll(bot_updated)
    if not bot:
        fail(f"robot account '{BOT_KEPT}' not found — it should have been updated, not deleted")
    dn = bot.get("DisplayName") or bot.get("displayName") or ""
    if dn != EXPECTED_DISPLAY_NAME:
        fail(f"robot '{BOT_KEPT}' display name not updated (got {dn!r}, expected "
             f"{EXPECTED_DISPLAY_NAME!r})")
    if str(_id_of(bot)) != bot_update_id:
        fail(f"'{BOT_KEPT}' has id={_id_of(bot)} but the seeded robot was {bot_update_id} — it was "
             "recreated, not updated in place")

    # Prove the delete by fetching the id DIRECTLY. robots() filters with
    # `--search ce-identity-maintain`, which matches on NAME, so a robot renamed
    # out of that window (zz-archived-bot, decommissioned-2026-08) is simply
    # absent from the result set and an id-membership test on it passes — the
    # exact archive-instead-of-delete hole this assertion exists to close.
    got = run_cli(["admin", "robot-accounts", "get", bot_retire_id])
    if got and got.get("Result") == "Success":
        payload = got.get("Data") or {}
        fail(f"the retired robot (id={bot_retire_id}) still exists as "
             f"'{_name(payload) or '?'}' — it was renamed or left in place, not deleted")
    if got is None:
        # run_cli returns None for a genuine not-found AND for a transport error,
        # so a None alone is not proof of deletion. Confirm against an UNFILTERED
        # page, which a rename cannot hide from.
        page = run_cli(["admin", "robot-accounts", "list", "--limit", LIST_LIMIT])
        if not page or page.get("Result") != "Success":
            fail(f"could not confirm the retired robot (id={bot_retire_id}) is gone: "
                 "`get` returned no result and the unfiltered list could not be read")
        all_ids = {str(_id_of(r)) for r in page.get("Data", []) if _id_of(r)}
        if bot_retire_id in all_ids:
            surviving = next((_name(r) for r in page.get("Data", [])
                              if str(_id_of(r)) == bot_retire_id), "?")
            fail(f"the retired robot (id={bot_retire_id}) still exists as '{surviving}' — it was "
                 "renamed or left in place, not deleted")

    builtins_present = sum(1 for g in gs if _is_builtin(g))

    ok(f"seed baseline: {len(expected_others)} non-fixture groups, fixture ids rename={rename_id} "
       f"stale={stale_id} bot={bot_update_id} retired={bot_retire_id} | group {rename_id} renamed "
       f"IN PLACE to '{GROUP_RENAMED}' | stale id {stale_id} absent | robot {bot_update_id} "
       f"display name = {dn!r} | retired id {bot_retire_id} absent | all "
       f"{len(expected_others)} non-fixture groups intact ({builtins_present} built-in) across "
       f"{len(gs)} listed groups")


main()
