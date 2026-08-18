#!/usr/bin/env python3
"""Verify the identity-maintain e2e outcome by reading tenant state back.

Four independent assertions, all outcome-graded (never a command string):

  1. groups update  — 'ce-identity-maintain-group-renamed' exists and the
                      pre-seeded 'ce-identity-maintain-group' name is gone.
  2. groups delete  — 'ce-identity-maintain-stale-group' is gone.
  3. robot update   — 'ce-identity-maintain-bot' still exists and its display
                      name is now 'Maintain Bot Updated' (seeded as
                      'Maintain Bot'), proving a real update landed.
  4. robot delete   — 'ce-identity-maintain-retired-bot' is gone.

Also asserts at least one BuiltIn group survived (SKILL.md anti-pattern 1:
built-in groups must never be deleted).
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_identity_maintained: %(message)s")

GROUP_SEEDED = "ce-identity-maintain-group"
GROUP_RENAMED = "ce-identity-maintain-group-renamed"
GROUP_STALE = "ce-identity-maintain-stale-group"
BOT_KEPT = "ce-identity-maintain-bot"
BOT_RETIRED = "ce-identity-maintain-retired-bot"
EXPECTED_DISPLAY_NAME = "Maintain Bot Updated"


def _name(item):
    return item.get("Name") or item.get("name") or item.get("displayName") or ""


def groups():
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data", [])


def robots():
    data = run_cli(["admin", "robot-accounts", "list", "--search", "ce-identity-maintain"])
    if not data or data.get("Result") != "Success":
        return None
    return data.get("Data", [])


def main():
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
    if GROUP_SEEDED in group_names:
        fail(f"group still named '{GROUP_SEEDED}' — a new group was created instead of renaming the existing one")
    if GROUP_STALE in group_names:
        fail(f"group '{GROUP_STALE}' still exists — it was not deleted")
    if not any((g.get("Type") or g.get("type") or "") == "BuiltIn" for g in gs):
        fail("no BuiltIn group left on the tenant — built-in groups must never be deleted")

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
        fail(f"robot '{BOT_KEPT}' display name not updated (got {dn!r}, expected {EXPECTED_DISPLAY_NAME!r})")

    rs = robots()
    if rs is None:
        fail("could not list robot accounts — cannot verify the retired bot is gone")
    if any(_name(r) == BOT_RETIRED for r in rs):
        fail(f"robot account '{BOT_RETIRED}' still exists — it was not deleted")

    ok(f"group renamed to '{GROUP_RENAMED}', '{GROUP_STALE}' deleted, "
       f"robot '{BOT_KEPT}' display name = {dn!r}, '{BOT_RETIRED}' deleted")


main()
