#!/usr/bin/env python3
"""Pre-run seed for authz assignment tests: grant a role to the login identity so
the agent has a real assignment to revoke.

  AUTHZ_ASSIGNMENT_ROLE_KEY     seed.json key of a role this run seeded, whose
                                grant is being set up (use this, or ROLE_NAME for
                                a platform built-in)
  AUTHZ_ASSIGNMENT_ROLE_NAME    exact role name, for built-in roles that carry no
                                run suffix
  AUTHZ_ASSIGNMENT_ROLE_TYPE    Custom | BuiltIn (default Custom)
  AUTHZ_ASSIGNMENT_SCOPE_PATH   scope path; `<TID>` expands to the login tenant
                                (default `/tenant/<TID>`, `/` for organization)
  AUTHZ_SEED_KEY                seed.json key to record the grant under

Idempotent: an existing grant of the same role to the same identity at the same
path is removed first, then re-created, so the recorded id always belongs to this
run. The state file is cleared up-front and written only after the grant is read
back from the tenant — verify_authz_assignment_deleted.py treats a missing state
file as an error, so a failed seed cannot make the revoke check pass for free.

Always exits 0.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from admin_helpers import (
    assignments_at, login_info, poll, resolve_scope_path, roles_matching, run_cli,
    seed_entry, update_seed,
)

logging.basicConfig(level=logging.INFO, format="setup_authz_assignment: %(message)s")
logger = logging.getLogger(__name__)


def main():
    role_type = (os.environ.get("AUTHZ_ASSIGNMENT_ROLE_TYPE") or "Custom").strip()
    seed_key = (os.environ.get("AUTHZ_SEED_KEY") or "").strip()
    role_key = (os.environ.get("AUTHZ_ASSIGNMENT_ROLE_KEY") or "").strip()
    role_name = (os.environ.get("AUTHZ_ASSIGNMENT_ROLE_NAME") or "").strip()

    # A role this run seeded carries the run suffix; look its real name up rather
    # than guessing, so a peer run's identically-based role is never picked.
    if role_key:
        entry = seed_entry(role_key)
        if not entry:
            logger.warning("seed.json has no '%s' entry — skipping grant seed", role_key)
            return
        role_name = entry["name"]
    if not role_name or not seed_key:
        logger.warning("AUTHZ_SEED_KEY plus one of AUTHZ_ASSIGNMENT_ROLE_KEY / "
                       "AUTHZ_ASSIGNMENT_ROLE_NAME are required — skipping seed")
        return

    identity = login_info()
    identity_id = identity.get("UserId")
    if not identity_id:
        logger.warning("Could not resolve the login identity — skipping seed")
        return
    scope_path = resolve_scope_path(
        os.environ.get("AUTHZ_ASSIGNMENT_SCOPE_PATH"), identity.get("TenantId")
    )

    roles = roles_matching(role_name, role_type=role_type)
    if not roles:
        logger.warning("Role '%s' (%s) not found — skipping seed", role_name, role_type)
        return
    role_id = roles[0].get("Id") or roles[0].get("id")

    for existing in assignments_at(identity_id, scope_path):
        if existing.get("RoleName") == role_name and existing.get("Id"):
            logger.info("Removing leftover grant of '%s' (id=%s)", role_name, existing["Id"])
            run_cli(["admin", "authorization", "roles", "assignments", "delete", existing["Id"]])

    res = run_cli([
        "admin", "authorization", "roles", "assignments", "create",
        "--role-id", role_id, "--identity-id", identity_id,
        "--identity-type", "User", "--scope-path", scope_path,
    ])
    if not res or res.get("Result") != "Success":
        logger.warning("Seed grant failed for '%s' at %s: %s", role_name, scope_path, res)
        return

    def created():
        for a in assignments_at(identity_id, scope_path):
            if a.get("RoleName") == role_name and a.get("Id"):
                return a
        return None

    grant = poll(created)
    if not grant:
        logger.warning("Seed grant of '%s' not visible at %s after retries", role_name, scope_path)
        return

    logger.info("Seeded grant of '%s' to %s at %s (id=%s)", role_name, identity_id, scope_path, grant["Id"])
    update_seed(**{seed_key: {"id": grant["Id"], "role": role_name,
                              "scope": scope_path, "identity": identity_id}})


main()
sys.exit(0)
