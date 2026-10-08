#!/usr/bin/env python3
"""pre_run: point this task's `uip` at another tenant of the same organization.

Usage:
    use_tenant.py <tenant-name>

Some scenarios need tenant settings that cannot coexist with the default tenant's
(e.g. a Business Process schema without `new_applications`), so they run on a
second tenant in the same organization. CI logs in once and mounts one `~/.uipath`
into every sandbox, read-write, so switching it with `uip login tenant set` would
move every concurrent task. Instead this copies the login to a private directory
OUTSIDE the sandbox (the copy holds the access token, and the sandbox is kept as a
run artifact), rewrites the tenant there, and records that directory in
`.ah-tenant-home`. The `.uip-recorder` shim and ah_cli.py both run the real CLI
with HOME set to it; nothing else changes.

The CLI's login token is organization-scoped, so the same login serves any tenant
of the organization where the identity has access.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ah_cli import (  # noqa: E402
    TENANT_HOME_MARKER,
    describe_failure,
    items,
    precondition_failed,
    succeeded,
    uip_json,
)

AUTH_FILE = ".auth"


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
    if os.path.exists(TENANT_HOME_MARKER):
        precondition_failed(f"{TENANT_HOME_MARKER} already exists; use_tenant.py must run once, first")

    source = os.path.join(os.path.expanduser("~"), ".uipath")
    if not os.path.isfile(os.path.join(source, AUTH_FILE)):
        precondition_failed(f"no {AUTH_FILE} login file under {source}; a second tenant needs a file login")
    target_id = tenant_id(name)

    home = tempfile.mkdtemp(prefix="ah-tenant-")
    login = os.path.join(home, ".uipath")
    shutil.copytree(source, login)
    auth_path = os.path.join(login, AUTH_FILE)
    with open(auth_path, encoding="utf-8") as handle:
        auth = handle.read()
    for key, value in (("UIPATH_TENANT_NAME", name), ("UIPATH_TENANT_ID", target_id)):
        auth, count = re.subn(rf"^{key}=.*$", f"{key}={value}", auth, flags=re.M)
        if count != 1:
            precondition_failed(f"{AUTH_FILE} has {count} {key} lines; expected exactly one")
    with open(auth_path, "w", encoding="utf-8") as handle:
        handle.write(auth)
    os.chmod(auth_path, 0o600)

    with open(TENANT_HOME_MARKER, "w", encoding="utf-8") as handle:
        handle.write(home)

    status = uip_json(["login", "status"])
    active = (status.get("Data") or {}).get("Tenant")
    if not succeeded(status) or str(active).lower() != name.lower():
        precondition_failed(f"login copy does not resolve to {name} (got {active!r}): {describe_failure(status)}")
    print(f"use_tenant: uip now targets tenant {name} ({target_id})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
