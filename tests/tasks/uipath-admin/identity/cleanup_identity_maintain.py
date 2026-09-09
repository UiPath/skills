#!/usr/bin/env python3
"""Best-effort teardown for the identity-maintain e2e: delete the marker groups
and robot accounts, whatever state the run left them in.

Exact-name matching (not substring) so a parallel run (-jN) cannot sweep a
sibling test's fixtures. Always exits 0 — failures here never affect pass/fail.
"""

import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_identity_maintain: %(message)s")
logger = logging.getLogger(__name__)

GROUPS = (
    "ce-identity-maintain-group",
    "ce-identity-maintain-group-renamed",
    "ce-identity-maintain-stale-group",
)
BOTS = (
    "ce-identity-maintain-bot",
    "ce-identity-maintain-retired-bot",
)
MEMBER_EMAIL = "ce-identity-maintain-member@example.com"
MEMBER_SEARCH = "ce-identity-maintain-member"
# robot-accounts/users list default to 20; without this, leaked fixtures past
# page 1 are never cleaned up.
LIST_LIMIT = "200"


def _id(item):
    return item.get("Id") or item.get("id")


def _name(item):
    return item.get("Name") or item.get("name") or item.get("displayName") or ""


STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_identity_maintain_seed.json")


def sweep_seeded_ids():
    """Delete seeded groups/robots BY ID, which a rename cannot hide.

    Same rationale as cleanup_extapp_maintain.sweep_seeded_ids: exact-name
    cleanup misses an object renamed instead of deleted, orphaning it on a shared
    org.
    """
    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError):
        return
    for key, kind in (("group_rename_id", "groups"), ("group_stale_id", "groups"),
                      ("bot_update_id", "robot-accounts"), ("bot_retire_id", "robot-accounts")):
        oid = state.get(key)
        if not oid:
            continue
        got = run_cli(["admin", kind, "get", str(oid)])
        if got and got.get("Result") == "Success":
            logger.info("Deleting seeded %s by id %s (survived name-based cleanup)", kind, oid)
            run_cli(["admin", kind, "delete", str(oid)])


def main():
    data = run_cli(["admin", "groups", "list"])
    if data and data.get("Result") == "Success":
        for g in data.get("Data", []):
            if _name(g) in GROUPS and _id(g):
                logger.info("Deleting group '%s' (id=%s)", _name(g), _id(g))
                run_cli(["admin", "groups", "delete", _id(g)])
    else:
        logger.warning("Could not list groups — skipping group cleanup")

    data = run_cli(["admin", "robot-accounts", "list", "--search", "ce-identity-maintain",
                   "--limit", LIST_LIMIT])
    if data and data.get("Result") == "Success":
        for r in data.get("Data", []):
            if _name(r) in BOTS and _id(r):
                logger.info("Deleting robot account '%s' (id=%s)", _name(r), _id(r))
                run_cli(["admin", "robot-accounts", "delete", _id(r)])
    else:
        logger.warning("Could not list robot accounts — skipping robot cleanup")

    # The dedicated fixture member invited by setup. Exact email match — this must
    # never touch a real org user.
    data = run_cli(["admin", "users", "list", "--search", MEMBER_SEARCH, "--limit", LIST_LIMIT])
    if data and data.get("Result") == "Success":
        for u in data.get("Data", []):
            email = (u.get("Email") or u.get("email") or "").lower()
            if email == MEMBER_EMAIL and _id(u):
                logger.info("Deleting fixture member user '%s' (id=%s)", email, _id(u))
                run_cli(["admin", "users", "delete", _id(u)])
    else:
        logger.warning("Could not list users — skipping fixture-member cleanup")


main()
sweep_seeded_ids()
sys.exit(0)
