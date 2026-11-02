#!/usr/bin/env python3
"""Shared grader over the `uip` shim's state: exit 0 when the check holds.

    python3 mocks/check_state.py enabled|disabled|restored   # on the login's tenant
    python3 mocks/check_state.py enabled-everywhere          # on every tenant in the org
    python3 mocks/check_state.py assigned [PRODUCT]          # a pack policy the agent
                                                             # created, on the login's tenant

"My tenant" in the prompts is the one the recorded login is on, so a state
change on another tenant the login can see, or at organization scope, does not
count. One script, so the tenant rule cannot drift between tasks.
"""

import json
import os
import sys

MOCKS = os.path.dirname(os.path.abspath(__file__))
PACK = "iso-42001-2023"


def fixture(name):
    with open(os.path.join(MOCKS, "fixtures", f"{name}.json")) as fh:
        return json.load(fh)


def holds(check, args):
    path = os.path.join(MOCKS, "state.json")
    state = json.load(open(path)) if os.path.exists(path) else {}
    tenant = fixture("login-status")["Data"]["TenantId"]
    if check in ("enabled", "disabled", "restored"):
        return tenant in state.get(check, [])
    if check == "enabled-everywhere":
        return set(state.get("enabled", [])) >= {t["TenantId"] for t in fixture("tenant-list")["Data"]}
    if check == "assigned":
        product = args[0] if args else None
        created = {i for i, r in state.get("policies", {}).items() if r["Name"].startswith(f"{PACK}-")}
        return any(a["TenantIdentifier"] == tenant and a["PolicyIdentifier"] in created
                   and product in (None, a["ProductIdentifier"])
                   for a in state.get("assignments") or [])
    raise SystemExit(f"check_state.py: unknown check {check!r}")


if __name__ == "__main__":
    sys.exit(0 if len(sys.argv) > 1 and holds(sys.argv[1], sys.argv[2:]) else 1)
