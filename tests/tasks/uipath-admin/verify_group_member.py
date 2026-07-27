#!/usr/bin/env python3
"""Verify the marker group has at least one member after the agent added a user."""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, poll, fail, ok, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="verify_group_member: %(message)s")

GROUP = "ce-identity-smoke-group"


def find_group():
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for g in data.get("Data", []):
        if (g.get("Name") or g.get("name") or "") == GROUP:
            return g
    return None


def main():
    g = poll(find_group)
    if not g:
        fail(f"group '{GROUP}' not found — setup may have failed")
    gid = g.get("Id") or g.get("id")

    def has_member():
        data = run_cli(["admin", "groups", "members", "list", gid])
        if not data or data.get("Result") != "Success":
            return None
        members = _first_list(data.get("Data"))
        return members if (members and len(members) > 0) else None

    m = poll(has_member)
    if not m:
        fail(f"group '{GROUP}' has no members — agent did not add a user")
    ok(f"group '{GROUP}' has {len(m)} member(s)")


main()
