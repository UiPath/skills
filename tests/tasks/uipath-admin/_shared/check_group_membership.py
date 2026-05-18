#!/usr/bin/env python3
"""Verify the 'Invoice Processing Team' group exists and has at least one member."""

import json
import subprocess
import sys


def run_cli(args: list[str]) -> dict:
    result = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=30,
    )
    return json.loads(result.stdout)


def main():
    # 1. Find the group
    groups = run_cli(["admin", "groups", "list"])
    assert groups["Result"] == "Success", f"groups list failed: {groups}"

    target = None
    for g in groups["Data"]:
        if "Invoice Processing Team" in (g.get("name", "") or g.get("displayName", "")):
            target = g
            break

    if target is None:
        print("FAIL: 'Invoice Processing Team' group not found")
        sys.exit(1)

    group_id = target.get("id")
    print(f"OK: Found group '{target.get('name')}' (id={group_id})")

    # 2. Check membership
    members = run_cli(["admin", "groups", "members", "list", group_id])
    assert members["Result"] == "Success", f"members list failed: {members}"

    member_count = len(members.get("Data", []))
    if member_count < 1:
        print(f"FAIL: Group has {member_count} members, expected at least 1")
        sys.exit(1)

    print(f"OK: Group has {member_count} member(s)")


if __name__ == "__main__":
    main()
