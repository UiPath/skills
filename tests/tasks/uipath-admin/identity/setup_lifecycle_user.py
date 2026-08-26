#!/usr/bin/env python3
"""Pre-run seed for the user-lifecycle smoke: (re)invite the marker user with an
initial surname, so the agent's job is a genuine UPDATE (not an invite folded
with --surname). Verify then proves the surname changed. Always exits 0."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="setup_lifecycle_user: %(message)s")
logger = logging.getLogger(__name__)

MARKER_EMAIL = "ce-identity-lifecycle@example.com"
INITIAL_SURNAME = "LifecycleUser"


def main():
    # Remove any leftover marker user first (idempotent seed).
    data = run_cli(["admin", "users", "list", "--search", "ce-identity-lifecycle"])
    if data and data.get("Result") == "Success":
        for u in data.get("Data", []):
            if (u.get("Email") or u.get("email") or "").lower() == MARKER_EMAIL:
                uid = u.get("Id") or u.get("id")
                if uid:
                    run_cli(["admin", "users", "delete", uid])

    res = run_cli(["admin", "users", "invite", "--email", MARKER_EMAIL,
                   "--name", "Test", "--surname", INITIAL_SURNAME])
    logger.info("Seeded lifecycle user '%s' (surname=%s): %s",
                MARKER_EMAIL, INITIAL_SURNAME, (res or {}).get("Result"))


main()
sys.exit(0)
