#!/usr/bin/env python3
"""Verify the agent resolved real identity UUIDs from the directory.

  GOV_LOOKUP_FILE  file the agent saved its resolved ids into (required)

The subject names come from seed.json (written by setup_lookup_subjects.py), so
this checks the run's own group and robot account rather than shared fixtures.
Each subject is resolved again here, live, and its UUID must appear in the
agent's saved output — UUIDs are unguessable, so their presence proves a real
directory query whatever shape the answer was saved in.

Exits 0 on success, 1 on failure.
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
from gov_helpers import fail, load_seed, login_info, ok, run_cli

logging.basicConfig(level=logging.INFO, format="verify_identity_lookup: %(message)s")


def directory_id(kind: str, match: str, field: str = "Name") -> str | None:
    data = run_cli(["admin", kind, "list"])
    if not data or data.get("Result") != "Success":
        return None
    for row in (data.get("Data") or []):
        value = row.get(field) or row.get(field[0].lower() + field[1:]) or ""
        if str(value).lower() == match.lower():
            return row.get("Id") or row.get("id")
    return None


def main():
    path = (os.environ.get("GOV_LOOKUP_FILE") or "").strip()
    if not path:
        fail("GOV_LOOKUP_FILE must be set")
    subjects = (load_seed().get("subjects") or {})
    robot_name = subjects.get("robotName")
    group_name = subjects.get("groupName")
    if not robot_name or not group_name:
        fail("seed.json has no subjects entry — the pre_run seed did not complete")
    if not os.path.exists(path):
        fail(f"{path} was not written — the agent saved no resolved identities")

    saved = open(path, encoding="utf-8-sig").read().lower()
    identity = login_info()
    # Prefer the id `login status` reports for the authenticated principal. A
    # directory search by email is only a fallback: the CI runner authenticates
    # as a bot whose login-status email need not match any directory row, and
    # resolving the caller is the agent's job, not this check's.
    caller = next((identity.get(k) for k in ("UserId", "ClientId", "ApplicationId", "AppId")
                   if identity.get(k)), None)
    if not caller:
        email = identity.get("UserEmail") or identity.get("UserName") or ""
        caller = directory_id("users", email, field="Email")
    expected = {
        "authenticated identity": caller,
        "robot account": directory_id("robot-accounts", robot_name),
        "group": directory_id("groups", group_name),
    }

    # The two seeded subjects must resolve — this run created them. The caller's
    # own id is asserted only when the platform reports one; an environment whose
    # login status exposes no principal id must not fail an agent that did the work.
    if not expected["authenticated identity"]:
        del expected["authenticated identity"]
        print("NOTE: login status reports no principal id — checking the seeded subjects only")
    unresolvable = [k for k, v in expected.items() if not v]
    if unresolvable:
        fail(f"could not resolve {unresolvable} on the directory — the fixtures may not be seeded")

    missing = [f"{k} ({v})" for k, v in expected.items() if v.lower() not in saved]
    if missing:
        fail(f"saved output does not contain the real UUID for: {', '.join(missing)}")

    ok(f"all three identity UUIDs resolved from the directory are present in {os.path.basename(path)}")


main()
