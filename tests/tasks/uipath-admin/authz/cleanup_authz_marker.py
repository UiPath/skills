#!/usr/bin/env python3
"""Best-effort cleanup for authz tests: revoke marker grants, then delete marker roles.

  AUTHZ_CLEANUP_MARKER       substring identifying test-owned custom roles, e.g.
                             `ce-authz-role`. Only objects that ALSO carry this
                             run's uuid8 suffix are removed.
  AUTHZ_CLEANUP_GRANT_ROLES  comma-separated exact role names (built-ins the test
                             granted, e.g. `Access Viewer`) to revoke from the
                             login identity. Optional.

CONCURRENCY: several agents run these tasks against one organization at the same
time, so cleanup must never touch a peer run's objects. Custom roles and their
grants are removed only when the name carries BOTH the marker and this run's
uuid8 (from seed.json). The exact-name grant list is the one exception — a
built-in role carries no suffix — so keep it to roles a single task owns.

Grants are revoked before roles are deleted so nothing is left dangling.

The agent's own delete/revoke steps are the primary path; this post_run is the
safety net for a run that failed midway. Always exits 0 — cleanup failures never
affect pass/fail.
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
from admin_helpers import assignments_at, login_info, owned_by_this_run, roles_matching, run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_authz_marker: %(message)s")
logger = logging.getLogger(__name__)


def revoke_grants(marker: str, exact_names: set[str]):
    identity = login_info()
    identity_id = identity.get("UserId")
    tenant_id = identity.get("TenantId")
    if not identity_id:
        logger.warning("Could not resolve the login identity — skipping grant cleanup")
        return

    paths = ["/"] + ([f"/tenant/{tenant_id}"] if tenant_id else [])
    seen = set()
    for path in paths:
        for a in assignments_at(identity_id, path):
            name = a.get("RoleName") or ""
            aid = a.get("Id")
            if not aid or aid in seen:
                continue
            mine = marker and marker in name and owned_by_this_run(name)
            if mine or name in exact_names:
                seen.add(aid)
                logger.info("Revoking '%s' at %s (id=%s)", name, a.get("Scope"), aid)
                run_cli(["admin", "authorization", "roles", "assignments", "delete", aid])


def delete_roles(marker: str):
    for role in roles_matching(marker, exact=False):
        if not owned_by_this_run(role.get("Name") or ""):
            continue  # a peer run's role — leave it alone
        role_id = role.get("Id") or role.get("id")
        if not role_id:
            continue
        logger.info("Deleting custom role '%s' (id=%s)", role.get("Name"), role_id)
        run_cli(["admin", "authorization", "roles", "delete", role_id])


def main():
    marker = (os.environ.get("AUTHZ_CLEANUP_MARKER") or "").strip()
    exact_names = {
        n.strip() for n in (os.environ.get("AUTHZ_CLEANUP_GRANT_ROLES") or "").split(",")
        if n.strip()
    }
    if not marker and not exact_names:
        logger.warning("Neither AUTHZ_CLEANUP_MARKER nor AUTHZ_CLEANUP_GRANT_ROLES set — nothing to do")
        return

    revoke_grants(marker, exact_names)
    if marker:
        delete_roles(marker)


main()
sys.exit(0)
