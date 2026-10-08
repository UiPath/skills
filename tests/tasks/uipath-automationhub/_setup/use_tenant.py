#!/usr/bin/env python3
"""pre_run: point this task's `uip` at another tenant of the same organization.

Usage:
    use_tenant.py <tenant-name>

Some scenarios need tenant settings that cannot coexist with the default tenant's
(e.g. a Business Process schema without `new_applications`), so they run on a
second tenant in the same organization. CI logs in once and shares one login file
with every sandbox, read-write, so switching it with `uip login tenant set` would
move every concurrent task. Instead this writes `.ah-tenant.json` (the tenant's
name and id, and where the shared login file is). The `.uip-recorder` shim and
ah_cli.py then run the real CLI through its env-var auth on that tenant, taking
the token and organization from the shared login file on each call. No token is
copied, and the shared login is never modified.

The CLI's login token is organization-scoped, so the same login serves any tenant
of the organization where the identity has access.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ah_cli import (  # noqa: E402
    TENANT_MARKER,
    describe_failure,
    items,
    precondition_failed,
    succeeded,
    uip_json,
)


def login_file() -> str:
    which = uip_json(["login", "which"])
    data = which.get("Data") or {}
    if not succeeded(which) or not data.get("Exists") or not data.get("Path"):
        precondition_failed(f"no login file for uip to switch tenants from: {describe_failure(which) or data}")
    return str(data["Path"])


def tenant_id(name: str) -> str:
    listing = uip_json(["login", "tenant", "list"])
    if not succeeded(listing):
        precondition_failed(f"uip login tenant list failed: {describe_failure(listing)}")
    for tenant in items(listing):
        if str(tenant.get("TenantName", "")).lower() == name.lower():
            return str(tenant["TenantId"])
    names = ", ".join(str(t.get("TenantName")) for t in items(listing))
    precondition_failed(f"tenant {name!r} is not in this organization (have: {names})")
    return ""  # unreachable: precondition_failed exits


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(f"usage: {sys.argv[0]} <tenant-name>", file=sys.stderr)
        return 2
    name = argv[0]
    if os.path.exists(TENANT_MARKER):
        precondition_failed(f"{TENANT_MARKER} already exists; use_tenant.py must run once, first")

    target = {"tenant_name": name, "tenant_id": tenant_id(name), "auth_file": login_file()}
    with open(TENANT_MARKER, "w", encoding="utf-8") as handle:
        json.dump(target, handle, indent=1)

    status = uip_json(["login", "status"])
    active = (status.get("Data") or {}).get("Tenant")
    if not succeeded(status) or str(active).lower() != name.lower():
        os.remove(TENANT_MARKER)
        precondition_failed(f"the switched login does not resolve to {name} (got {active!r}): {describe_failure(status)}")
    print(f"use_tenant: uip now targets tenant {name} ({target['tenant_id']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
