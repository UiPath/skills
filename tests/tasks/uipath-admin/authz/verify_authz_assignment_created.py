#!/usr/bin/env python3
"""Verify the agent granted a role to the login identity — read back from the tenant.

  AUTHZ_ASSIGNMENT_ROLE_KEY    seed.json key of a role this run seeded, whose
                               grant is expected (use this, or ROLE_NAME for a
                               platform built-in)
  AUTHZ_ASSIGNMENT_ROLE_NAME   exact role name, for built-ins with no run suffix
  AUTHZ_ASSIGNMENT_SCOPE_PATH  scope path the grant must sit at; `<TID>` expands
                               to the login tenant (default `/tenant/<TID>`)

Read-back uses `assignments list --scope-path <path> --identity-id <id>`. The
composed `--scope Organization|Tenant` form also pins serviceName, which hides
grants of roles owned by another service (every built-in role among them), so the
verbatim path is the only reliable way to see the grant the agent just made.

Exits 0 on success, 1 on failure.
"""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import assignments_at, fail, login_info, ok, poll, resolve_scope_path, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_authz_assignment_created: %(message)s")


def main():
    role_key = (os.environ.get("AUTHZ_ASSIGNMENT_ROLE_KEY") or "").strip()
    role_name = (os.environ.get("AUTHZ_ASSIGNMENT_ROLE_NAME") or "").strip()
    if role_key:
        entry = seed_entry(role_key)
        if not entry:
            fail(f"seed.json has no '{role_key}' entry — the role was never seeded for this run")
        role_name = entry["name"]
    if not role_name:
        fail("AUTHZ_ASSIGNMENT_ROLE_KEY or AUTHZ_ASSIGNMENT_ROLE_NAME must be set")

    identity = login_info()
    identity_id = identity.get("UserId")
    if not identity_id:
        fail("could not resolve the login identity to verify the grant")
    scope_path = resolve_scope_path(
        os.environ.get("AUTHZ_ASSIGNMENT_SCOPE_PATH"), identity.get("TenantId")
    )

    def granted():
        for a in assignments_at(identity_id, scope_path):
            if a.get("RoleName") == role_name:
                return a
        return None

    grant = poll(granted)
    if not grant:
        seen = sorted({a.get("RoleName") for a in assignments_at(identity_id, scope_path)})
        fail(f"'{role_name}' is not assigned to {identity_id} at {scope_path} — "
             f"roles found there: {seen}")

    if (grant.get("Scope") or "").lower() != scope_path.lower():
        fail(f"'{role_name}' is assigned at {grant.get('Scope')!r}, expected {scope_path!r}")

    ok(f"'{role_name}' assigned to {identity_id} at {scope_path} (id={grant.get('Id')})")


main()
