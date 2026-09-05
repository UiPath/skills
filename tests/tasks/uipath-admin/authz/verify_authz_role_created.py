#!/usr/bin/env python3
"""Verify the agent created the requested custom role — read back from the tenant.

  AUTHZ_SEED_KEY           seed.json key holding this run's role name — written by
                           setup_authz_role.py, either as a plan (create
                           scenarios) or as a seeded object (required)
  AUTHZ_EXPECT_SCOPE       Organization | Tenant | TenantGlobal (required)
  AUTHZ_EXPECT_PERMISSION  action name the role must grant (required)
  AUTHZ_EXPECT_DESCRIPTION expected description, exact match (optional)

The role is located by name, then fetched by id (`roles get`) so the assertions
run against the tenant's own record, not the agent's transcript.

Scope is checked on the stored shape rather than the flag the agent typed:
Organization roles report ScopeType=Organization; Tenant and TenantGlobal roles
both report ScopeType=Tenant and are told apart by TenantId — a real tenant id
binds the role to one tenant, the all-zero id marks the cross-tenant template.

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
from admin_helpers import fail, login_info, ok, poll, role_get, roles_matching, seed_entry

logging.basicConfig(level=logging.INFO, format="verify_authz_role_created: %(message)s")

ZERO_GUID = "00000000-0000-0000-0000-000000000000"


def check_scope(role: dict, expected: str) -> str | None:
    """Return an error message when the role's stored shape != expected scope."""
    scope_type = (role.get("ScopeType") or "").lower()
    tenant_id = (role.get("TenantId") or "").lower()
    if expected == "Organization":
        if scope_type != "organization":
            return f"expected an Organization-scope role, tenant reports ScopeType={role.get('ScopeType')!r}"
        return None
    if scope_type != "tenant":
        return f"expected a Tenant-shape role, tenant reports ScopeType={role.get('ScopeType')!r}"
    if expected == "TenantGlobal":
        if tenant_id != ZERO_GUID:
            return (f"expected a TenantGlobal template (all-zero TenantId), "
                    f"role is bound to tenant {role.get('TenantId')!r}")
        return None
    # expected == "Tenant"
    if tenant_id == ZERO_GUID:
        return "role was created as a TenantGlobal template; expected binding to one tenant"
    login_tenant = (login_info().get("TenantId") or "").lower()
    if login_tenant and tenant_id != login_tenant:
        return f"role is bound to tenant {role.get('TenantId')!r}, expected the login tenant {login_tenant!r}"
    return None


def main():
    seed_key = (os.environ.get("AUTHZ_SEED_KEY") or "").strip()
    expected_scope = (os.environ.get("AUTHZ_EXPECT_SCOPE") or "").strip()
    permission = (os.environ.get("AUTHZ_EXPECT_PERMISSION") or "").strip()
    expected_description = os.environ.get("AUTHZ_EXPECT_DESCRIPTION")

    if not seed_key or expected_scope not in ("Organization", "Tenant", "TenantGlobal") or not permission:
        fail("AUTHZ_SEED_KEY, AUTHZ_EXPECT_SCOPE and AUTHZ_EXPECT_PERMISSION must be set")
    entry = seed_entry(seed_key)
    if not entry or not entry.get("name"):
        fail(f"seed.json has no '{seed_key}' entry — nothing was planned or seeded for this run")
    # Only this run's object: the name carries the run suffix, so a concurrent
    # run's identically-based role can neither satisfy nor break this check.
    name = entry["name"]

    matches = poll(lambda: roles_matching(name) or None)
    if not matches:
        fail(f"no custom role named '{name}' on the tenant — the role was never created")
    role_id = matches[0].get("Id") or matches[0].get("id")

    role = poll(lambda: role_get(role_id))
    if not role:
        fail(f"role '{name}' (id={role_id}) could not be read back")

    scope_error = check_scope(role, expected_scope)
    if scope_error:
        fail(f"role '{name}': {scope_error}")

    actions = [a.get("Name") for a in (role.get("ActionDetails") or [])]
    if permission not in actions:
        fail(f"role '{name}' does not grant {permission} — actions on the tenant: {actions}")

    if expected_description is not None:
        actual = (role.get("Description") or "").strip()
        if actual != expected_description.strip():
            fail(f"role '{name}' description is {actual!r}, expected {expected_description.strip()!r}")

    ok(f"role '{name}' (id={role_id}) exists with scope={expected_scope}, permission={permission}")


main()
