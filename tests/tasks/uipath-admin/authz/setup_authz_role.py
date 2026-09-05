#!/usr/bin/env python3
"""Pre-run seed for authz role tests: create one marker custom role on the tenant.

Everything is supplied by the calling test via environment variables — nothing is
hardcoded, so every authz test reuses this one seed:

  AUTHZ_ROLE_BASE         base role name; the run's uuid8 is appended so
                          concurrent runs never collide (required)
  AUTHZ_SEED_KEY          seed.json key to record this role under, e.g. `role`
                          or `stale_role` (required)
  AUTHZ_ROLE_PERMISSION   action name granted by the role (required)
  AUTHZ_ROLE_SCOPE        Organization | Tenant | TenantGlobal (optional when
                          AUTHZ_ROLE_SERVICE is set)
  AUTHZ_ROLE_SERVICE      owning service slug, e.g. documentunderstanding
                          (optional; scope is inferred from the service registry)
  AUTHZ_ROLE_DESCRIPTION  initial description (optional)
  AUTHZ_ROLE_PLAN_ONLY    set to 1 for a create-scenario: publish the run-scoped
                          name into seed.json for the agent to use, and create
                          nothing (the agent's own create is what is graded)

The created role is recorded in `seed.json` under AUTHZ_SEED_KEY, which the verify
scripts read. seed.json lives in the run's working directory, so two agents
running this task at the same time keep separate records and separate roles.

Nothing is deleted up-front: a same-named leftover cannot exist, because the name
carries this run's unique suffix. That also means a peer run's in-flight role is
never touched.

Always exits 0 — a seed failure surfaces as a failing criterion, not a harness error.
"""

import json
import logging
import os
import sys
import tempfile

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-admin", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from admin_helpers import run_cli, scoped, update_seed

logging.basicConfig(level=logging.INFO, format="setup_authz_role: %(message)s")
logger = logging.getLogger(__name__)


def main():
    base = (os.environ.get("AUTHZ_ROLE_BASE") or "").strip()
    seed_key = (os.environ.get("AUTHZ_SEED_KEY") or "").strip()
    permission = (os.environ.get("AUTHZ_ROLE_PERMISSION") or "").strip()
    scope = (os.environ.get("AUTHZ_ROLE_SCOPE") or "").strip()
    service = (os.environ.get("AUTHZ_ROLE_SERVICE") or "").strip()
    description = os.environ.get("AUTHZ_ROLE_DESCRIPTION") or ""
    if not base or not seed_key or not permission or not (scope or service):
        logger.warning(
            "AUTHZ_ROLE_BASE, AUTHZ_SEED_KEY, AUTHZ_ROLE_PERMISSION and one of "
            "AUTHZ_ROLE_SCOPE / AUTHZ_ROLE_SERVICE are required — skipping seed"
        )
        return
    name = scoped(base)

    if (os.environ.get("AUTHZ_ROLE_PLAN_ONLY") or "").strip() in ("1", "true", "yes"):
        # Create-scenario: the agent authors the role, so only publish the name it
        # must use. Run-scoped, so two agents on this task build different roles.
        update_seed(**{seed_key: {"name": name, "description": description,
                                  "permission": permission, "scope": scope or None}})
        logger.info("Planned role name '%s' for the agent to create", name)
        return

    actions_path = os.path.join(tempfile.gettempdir(), "authz_seed_actions.json")
    with open(actions_path, "w", encoding="utf-8") as fh:
        json.dump([permission], fh)

    args = ["admin", "authorization", "roles", "create", "--name", name, "--file", actions_path]
    if description:
        args += ["--description", description]
    if scope:
        args += ["--scope", scope]
    if service:
        args += ["--service", service]

    res = run_cli(args)
    role_id = ((res or {}).get("Data") or {}).get("CreatedRoleId")
    if not role_id:
        logger.warning("Seed create failed for role '%s': %s", name, res)
        return

    logger.info("Seeded role '%s' (id=%s, scope=%s, service=%s)", name, role_id, scope or "-", service or "-")
    update_seed(**{seed_key: {"id": role_id, "name": name, "description": description,
                              "permission": permission, "scope": scope or None}})


main()
sys.exit(0)
