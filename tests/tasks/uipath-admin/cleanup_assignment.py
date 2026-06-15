#!/usr/bin/env python3
"""Best-effort cleanup for authz role-assignment lifecycle tests.

Deletes the role assignment the test created: a built-in role granted to a User
principal at the test's scope. Both the role name and the scope are supplied by
the calling test via environment variables — nothing hardcoded:

  CLEANUP_ASSIGNMENT_ROLE   built-in role name the test assigns, e.g. "Viewer"
  CLEANUP_ASSIGNMENT_SCOPE  Organization | Tenant

The agent's own `roles assignments delete` is the primary cleanup; this post_run
is a safety net so a run that fails before its delete leaves no orphan grant.
Always exits 0 — failures here never affect pass/fail.

SAFETY: an assignment has no unique test-owned name (unlike a created role), so
this matches by (role name + User principal + not inherited) at the given scope.
On a shared tenant this could also remove a real user's direct assignment of the
same built-in role — it is intended for the dedicated e2e test account, and the
tests pin a narrow read-only role (Viewer / Access Viewer) to limit blast radius.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_assignment: %(message)s")
logger = logging.getLogger(__name__)

VALID_SCOPES = {"Organization", "Tenant"}


def main():
    role = (os.environ.get("CLEANUP_ASSIGNMENT_ROLE") or "").strip()
    scope = (os.environ.get("CLEANUP_ASSIGNMENT_SCOPE") or "").strip()
    if not role or scope not in VALID_SCOPES:
        logger.warning(
            "CLEANUP_ASSIGNMENT_ROLE must be set and CLEANUP_ASSIGNMENT_SCOPE one of %s — skipping cleanup",
            sorted(VALID_SCOPES),
        )
        return

    data = run_cli([
        "admin", "authorization", "roles", "assignments", "list", "--scope", scope,
    ])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list %s assignments — skipping cleanup", scope)
        return

    # assignments list returns Data = {..., Results: [ {Email, RoleAssignmentDtos: [...]}, ... ]}
    payload = data.get("Data") or {}
    principals = payload.get("Results", []) if isinstance(payload, dict) else (payload or [])
    targets = []
    for p in principals:
        for a in (p.get("RoleAssignmentDtos") or []):
            if (a.get("RoleName") == role
                    and a.get("SecurityPrincipalType") == "User"
                    and not a.get("Inherited", False)
                    and a.get("Id")):
                targets.append((a["Id"], p.get("Email") or p.get("DisplayName")))

    if not targets:
        logger.info("No User assignment of '%s' at %s scope — nothing to clean up", role, scope)
        return

    for assignment_id, who in targets:
        logger.info("Deleting assignment of '%s' to %s (id=%s)", role, who, assignment_id)
        result = run_cli(["admin", "authorization", "roles", "assignments", "delete", assignment_id])
        if result:
            logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
        else:
            logger.warning("Delete call returned no result for id=%s", assignment_id)


main()
sys.exit(0)
