#!/usr/bin/env python3
"""Verify a group's membership by reading it back from the live tenant.

Outcome check shared by the identity group tests — grades the membership end
state rather than trusting the agent's command string.

Env:
  GROUP_NAME      group to inspect (default: ce-identity-smoke-group, the smoke marker)
  EXPECT_MEMBERS  if set, require EXACTLY this many members; if unset, require >=1
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import run_cli, poll, fail, ok, first_list as _first_list

logging.basicConfig(level=logging.INFO, format="verify_group_member: %(message)s")

DEFAULT_GROUP = "ce-identity-smoke-group"


def find_group(name):
    data = run_cli(["admin", "groups", "list"])
    if not data or data.get("Result") != "Success":
        return None
    for g in data.get("Data", []):
        if (g.get("Name") or g.get("name") or "") == name:
            return g
    return None


def member_count(gid):
    """Live member list for the group, or None when the read itself failed."""
    data = run_cli(["admin", "groups", "members", "list", gid])
    if not data or data.get("Result") != "Success":
        return None
    members = _first_list(data.get("Data"))
    return members if members is not None else []


def main():
    group = os.environ.get("GROUP_NAME", DEFAULT_GROUP)
    expect_raw = (os.environ.get("EXPECT_MEMBERS") or "").strip()
    expect = int(expect_raw) if expect_raw else None

    g = poll(lambda: find_group(group))
    if not g:
        fail(f"group '{group}' not found — setup or the agent's create step may have failed")
    gid = g.get("Id") or g.get("id")

    # Poll until membership settles to the expected shape: group mutations are
    # eventually consistent, so a just-revoked member can linger for a beat.
    # Wrapped in a 1-tuple so a matched result is never mistaken for "not ready".
    def settled():
        members = member_count(gid)
        if members is None:
            return None  # read failed — retry
        if expect is None:
            return (members,) if len(members) > 0 else None
        return (members,) if len(members) == expect else None

    result = poll(settled)
    if result is None:
        latest = member_count(gid)
        actual = "unreadable" if latest is None else len(latest)
        if expect is None:
            fail(f"group '{group}' has no members — the add step did not take effect")
        fail(f"group '{group}' has {actual} member(s) — expected exactly {expect} "
             "after add-then-revoke; the membership end state is wrong")

    members = result[0]
    ok(f"group '{group}' has {len(members)} member(s), as expected"
       + (f" (exactly {expect})" if expect is not None else " (>=1)"))


main()
