#!/usr/bin/env python3
"""Verify a robot account with the smoke marker name was created on the tenant."""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli, poll, fail, ok

logging.basicConfig(level=logging.INFO, format="verify_robot: %(message)s")

MARKER = "ce-identity-smoke-bot"


def find():
    data = run_cli(["admin", "robot-accounts", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for r in data.get("Data", []):
        if (r.get("Name") or r.get("name") or "") == MARKER:
            return r
    return None


def main():
    r = poll(find)
    if not r:
        fail(f"no robot account named '{MARKER}' found — create may have failed")
    # Verify a display name was actually set (the --display-name flag), i.e. it
    # is present and distinct from the account name — not defaulted to the name.
    dn = r.get("DisplayName") or r.get("displayName") or ""
    if not dn or dn == MARKER:
        fail(f"robot '{MARKER}' created but no distinct display name set (DisplayName={dn!r})")
    ok(f"robot account '{MARKER}' created with display name {dn!r} (id={r.get('Id') or r.get('id')})")


main()
