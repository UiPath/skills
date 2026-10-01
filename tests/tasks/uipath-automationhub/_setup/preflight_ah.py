#!/usr/bin/env python3
"""pre_run: fail as ERROR, not FAILURE, when the Automation Hub tenant cannot take a publish.

Usage:
    preflight_ah.py [--require-non-admin]

Checks, all read-only and all through `uip ah`:
  - auth-info succeeds: AH is provisioned and onboarded for the active tenant, and
    the signed-in identity is active there with a role that can submit;
  - a "Business Process" idea flow exists (the publish flow's Step 2 default);
  - the category tree has at least one active, non-"Other" node;
  - the application inventory is readable.

`--require-non-admin` additionally insists the identity is NOT an AH admin, for
tasks that exercise the "applications 403 → publish anyway" fallback — an admin
would create the applications instead and the regression would go untested.

Writes `ah-preflight.json` (tenant url, owner email, flow id, archive target) for
seed_publish.py and the graders. Mirrors uipath-maestro-case's preflight: a revoked
login or an asleep tenant must never be scored against the skill.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ah_cli import (  # noqa: E402
    active_categories,
    archive_target,
    business_process_flow,
    describe_failure,
    items,
    precondition_failed,
    succeeded,
    uip_json,
)

OUTPUT = "ah-preflight.json"
SUBMITTER_ROLES = {"ah-standard-user", "ah-authorized-user"}
ADMIN_ROLE = "ah-system-admin"


def main(argv: list[str]) -> int:
    require_non_admin = "--require-non-admin" in argv
    problems: list[str] = []

    auth = uip_json(["ah", "auth-info", "get"])
    if not succeeded(auth):
        precondition_failed(f"uip ah auth-info get failed: {describe_failure(auth)}")
    data = auth.get("Data") or {}
    tenant = data.get("Tenant") or {}
    user = data.get("User") or {}
    roles = set(user.get("Roles") or [])
    if user.get("IsActive") != 1:
        problems.append(f"identity is not active in Automation Hub (IsActive={user.get('IsActive')})")
    if not roles & SUBMITTER_ROLES:
        problems.append(f"identity has no submitter role; roles={sorted(roles)}")
    if require_non_admin and (user.get("IsAdmin") == 1 or ADMIN_ROLE in roles):
        problems.append("identity is an AH admin, but this task needs a non-admin to exercise the 403 fallback")
    if not tenant.get("Url"):
        problems.append("auth-info carries no Tenant.Url")

    flows = uip_json(["ah", "idea-flows", "list"])
    flow = business_process_flow(items(flows)) if succeeded(flows) else None
    if not succeeded(flows):
        problems.append(f"uip ah idea-flows list failed: {describe_failure(flows)}")
    elif flow is None:
        problems.append("no 'Business Process' idea flow on this tenant: "
                        + ", ".join(str(f.get("Name")) for f in items(flows)))

    categories = uip_json(["ah", "categories", "get"])
    if not succeeded(categories):
        problems.append(f"uip ah categories get failed: {describe_failure(categories)}")
    elif not active_categories((categories.get("Data") or {}).get("Categories") or []):
        problems.append("category tree has no active non-'Other' category")

    inventory = uip_json(["ah", "applications", "list", "--limit", "50"])
    if not succeeded(inventory):
        problems.append(f"uip ah applications list failed: {describe_failure(inventory)}")

    if problems:
        print("preflight_ah: ENVIRONMENT gap — this tenant/identity cannot take a publish:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    archive = archive_target(flow) if flow else None
    summary = {
        "tenant_url": tenant.get("Url"),
        "owner_email": user.get("Email"),
        "is_admin": bool(user.get("IsAdmin") == 1 or ADMIN_ROLE in roles),
        "business_process_flow_id": flow.get("Id") if flow else None,
        "archive_phase": archive[0] if archive else None,
        "archive_status": archive[1] if archive else None,
        "inventory": [{"Id": a.get("Id"), "Name": a.get("Name"), "Version": a.get("Version")}
                      for a in items(inventory)],
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)
    print(f"preflight_ah: OK — flow {summary['business_process_flow_id']} on {summary['tenant_url']}, "
          f"{len(summary['inventory'])} inventory applications"
          + ("" if archive else "; WARNING: no Archived status on the flow, cleanup will be a no-op"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
