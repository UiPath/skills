#!/usr/bin/env python3
"""Best-effort teardown for the identity-maintain e2e: delete the marker groups
and robot accounts, whatever state the run left them in.

Exact-name matching (not substring) so a parallel run (-jN) cannot sweep a
sibling test's fixtures. Always exits 0 — failures here never affect pass/fail.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
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


def _id(item):
    return item.get("Id") or item.get("id")


def _name(item):
    return item.get("Name") or item.get("name") or item.get("displayName") or ""


def main():
    data = run_cli(["admin", "groups", "list"])
    if data and data.get("Result") == "Success":
        for g in data.get("Data", []):
            if _name(g) in GROUPS and _id(g):
                logger.info("Deleting group '%s' (id=%s)", _name(g), _id(g))
                run_cli(["admin", "groups", "delete", _id(g)])
    else:
        logger.warning("Could not list groups — skipping group cleanup")

    data = run_cli(["admin", "robot-accounts", "list", "--search", "ce-identity-maintain"])
    if data and data.get("Result") == "Success":
        for r in data.get("Data", []):
            if _name(r) in BOTS and _id(r):
                logger.info("Deleting robot account '%s' (id=%s)", _name(r), _id(r))
                run_cli(["admin", "robot-accounts", "delete", _id(r)])
    else:
        logger.warning("Could not list robot accounts — skipping robot cleanup")

    # The dedicated fixture member invited by setup. Exact email match — this must
    # never touch a real org user.
    data = run_cli(["admin", "users", "list", "--search", MEMBER_SEARCH])
    if data and data.get("Result") == "Success":
        for u in data.get("Data", []):
            email = (u.get("Email") or u.get("email") or "").lower()
            if email == MEMBER_EMAIL and _id(u):
                logger.info("Deleting fixture member user '%s' (id=%s)", email, _id(u))
                run_cli(["admin", "users", "delete", _id(u)])
    else:
        logger.warning("Could not list users — skipping fixture-member cleanup")


main()
sys.exit(0)
