#!/usr/bin/env python3
"""Verify 'Invoice Processing Team' group exists and has exactly one member."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from admin_helpers import run_cli, find_one, fail, ok

logging.basicConfig(level=logging.INFO, format="check_group: %(message)s")


def main():
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        fail("groups list did not return Success")

    target = find_one(data, "Invoice Processing Team", ["name", "displayName"])
    if not target:
        fail("'Invoice Processing Team' group not found")

    group_id = target.get("id")
    if not group_id:
        fail("Group found but missing 'id' field")

    ok(f"Found group (id={group_id})")

    members = run_cli(["admin", "groups", "members", "list", group_id])
    if not members or members.get("Result") != "Success":
        fail("members list did not return Success")

    member_count = len(members.get("Data", []))
    if member_count != 1:
        fail(f"Expected 1 member after add+revoke, got {member_count}")

    ok(f"Group has {member_count} member(s)")


if __name__ == "__main__":
    main()
