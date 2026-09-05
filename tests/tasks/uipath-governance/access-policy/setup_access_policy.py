#!/usr/bin/env python3
"""Pre-run seed for access-policy scenario tests.

  GOV_SEED_KEY          key to record this policy under in seed.json (default "policy")
  GOV_POLICY_BASE       base name; the run's id is appended so concurrent runs
                        never collide on the shared organization (required)
  GOV_POLICY_DESCRIPTION  seeded description (read back by the checks)
  GOV_RESOURCE_TYPE     selector resource type (default Agent)
  GOV_ACTOR_PROCESS_TYPE  executable-rule type (default Flow)
  GOV_POLICY_PLAN_ONLY  "1" records the intended name WITHOUT creating anything —
                        for scenarios where the agent itself does the create

Every seeded policy is created with status Simulated: the service evaluates and
logs it but never enforces it, so seeding cannot gate real traffic on the shared
test organization. `Active` is never used here, and `Inactive`/`Draft` are
rejected by the service (HTTP 400) — Simulated is the only non-enforcing status.

Always exits 0: a failed seed leaves seed.json without the entry, so the
scenario's own check fails rather than passing for free.
"""

import logging
import os
import sys

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-governance", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from gov_helpers import (ap_by_name, ap_create, ap_definition, login_info, poll, run_id,
                         scoped, update_seed)

logging.basicConfig(level=logging.INFO, format="setup_access_policy: %(message)s")
logger = logging.getLogger(__name__)


def main():
    base = (os.environ.get("GOV_POLICY_BASE") or "").strip()
    if not base:
        logger.warning("GOV_POLICY_BASE is not set — nothing seeded")
        return
    key = (os.environ.get("GOV_SEED_KEY") or "policy").strip()
    description = (os.environ.get("GOV_POLICY_DESCRIPTION") or "Seeded by the access-policy suite").strip()
    resource_type = (os.environ.get("GOV_RESOURCE_TYPE") or "Agent").strip()
    process_type = (os.environ.get("GOV_ACTOR_PROCESS_TYPE") or "Flow").strip()
    plan_only = (os.environ.get("GOV_POLICY_PLAN_ONLY") or "").strip() == "1"

    name = scoped(base)
    entry = {"name": name, "description": description, "status": "Simulated",
             "resourceType": resource_type, "actorProcessType": process_type}

    if plan_only:
        update_seed(**{key: entry})
        logger.info("Run %s will author '%s' itself (nothing created)", run_id(), name)
        return

    identity = login_info()
    org, tenant, user = (identity.get("OrganizationId"), identity.get("TenantId"),
                         identity.get("UserId"))
    if not (org and tenant and user):
        logger.warning("Could not read org/tenant/user from `uip login status` — nothing seeded")
        return

    created = ap_create(ap_definition(
        name=name, description=description, org_id=org, tenant_id=tenant,
        actor_user_id=user, resource_type=resource_type,
        actor_process_type=process_type, status="Simulated",
    ))
    if not created:
        logger.warning("Create failed for '%s' — nothing recorded in seed.json", name)
        return

    entry["id"] = created.get("Id")
    # Confirm the policy is queryable before handing the run to the agent: a
    # scenario that asks the agent to find it by name would otherwise race the
    # service's own propagation into `list`.
    if not poll(lambda: ap_by_name(name), max_attempts=6, delay=3):
        logger.warning("Policy '%s' was created but is not listable yet", name)
    update_seed(**{key: entry})
    logger.info("Seeded Simulated policy '%s' (id=%s)", name, entry["id"])


main()
sys.exit(0)
