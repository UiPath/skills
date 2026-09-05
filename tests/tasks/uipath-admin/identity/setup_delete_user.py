#!/usr/bin/env python3
"""Pre-run seed for the user-delete smoke: (re)invite the marker user the agent
will be asked to delete. Records the created user's id to a state file so the
verify step can prove the seed existed — otherwise a do-nothing agent would
"pass" because the user is trivially absent. Always exits 0 (best-effort seed).

Assumes serial execution: the marker email and the state-file name are fixed
(org-wide singletons), so two concurrent instances of this task on the same org
would race the shared user record. This matches the repo's sequential-run rule
and the other single-marker identity tests; salt both if parallelism is enabled."""

import logging
import os
import sys
import tempfile
import time

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli, poll

logging.basicConfig(level=logging.INFO, format="setup_delete_user: %(message)s")
logger = logging.getLogger(__name__)

MARKER_EMAIL = "ce-identity-delete@example.com"
SEARCH = "ce-identity-delete"
STATE_FILE = os.path.join(tempfile.gettempdir(), "ce_delete_user_seed.txt")


def find_user():
    data = run_cli(["admin", "users", "list", "--search", SEARCH])
    if not data or data.get("Result") != "Success":
        return None
    for u in data.get("Data", []):
        if (u.get("Email") or u.get("email") or "").lower() == MARKER_EMAIL:
            return u
    return None


def main():
    # Clear any stale state from a prior run in this container.
    try:
        os.remove(STATE_FILE)
    except OSError:
        pass

    # Remove any leftover marker user first (idempotent seed).
    u = find_user()
    if u:
        uid = u.get("Id") or u.get("id")
        if uid:
            run_cli(["admin", "users", "delete", uid])
            # Wait for the delete to propagate before re-inviting the same email
            # — otherwise the invite can collide ("already exists") and the seed
            # fails, which would false-FAIL a correct agent at verify time.
            for _ in range(4):
                if not find_user():
                    break
                time.sleep(3)

    res = run_cli(["admin", "users", "invite", "--email", MARKER_EMAIL,
                   "--name", "Test", "--surname", "DeleteUser"])
    if not res or res.get("Result") != "Success":
        logger.warning("Seed user invite failed: %s", res)
        return

    # Resolve the invited user's id and record it as authoritative proof of the
    # seed. User provisioning is eventually-consistent — poll so a listing lag
    # does not leave verify with no state file (which would fail a correct agent).
    u = poll(find_user)
    seed_id = (u.get("Id") or u.get("id")) if u else None
    if seed_id:
        with open(STATE_FILE, "w") as f:
            f.write(seed_id)
        logger.info("Seeded delete-target user '%s' id=%s", MARKER_EMAIL, seed_id)
    else:
        logger.warning("Could not resolve seeded user id")


main()
sys.exit(0)
