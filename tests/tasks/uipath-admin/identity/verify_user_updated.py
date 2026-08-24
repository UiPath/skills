#!/usr/bin/env python3
"""Verify the lifecycle user was invited AND updated (surname changed).

Reads the user back from the tenant and asserts it exists with the updated
surname — proving both the invite and the update landed. The post_run cleanup
deletes the user.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_user_updated: %(message)s")

MARKER_EMAIL = "ce-identity-lifecycle@example.com"
EXPECTED_SURNAME = "UpdatedUser"


def find():
    data = run_cli(["admin", "users", "list", "--search", "ce-identity-lifecycle"])
    if not data or data.get("Result") != "Success":
        return None
    for u in data.get("Data", []):
        if (u.get("Email") or u.get("email") or "").lower() == MARKER_EMAIL:
            return u
    return None


def main():
    u = poll(find)
    if not u:
        fail(f"user '{MARKER_EMAIL}' not found — invite may have failed")
    surname = u.get("Surname") or u.get("surname") or ""
    if surname != EXPECTED_SURNAME:
        fail(f"user found but surname not updated (got {surname!r}, expected {EXPECTED_SURNAME!r})")
    ok(f"user '{MARKER_EMAIL}' invited and updated (surname={surname})")


main()
