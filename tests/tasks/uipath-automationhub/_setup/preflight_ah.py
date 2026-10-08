#!/usr/bin/env python3
"""pre_run: fail as ERROR, not FAILURE, when the Automation Hub tenant cannot take a publish.

Usage:
    preflight_ah.py [--require-non-admin] [--require-new-applications | --require-no-new-applications]
                    [--require-app NAME ...] [--require-no-app NAME ...]

Checks, all read-only and all through `uip ah`:
  - auth-info succeeds: AH is provisioned and onboarded for the active tenant, and
    the signed-in identity is active there with a role that can submit;
  - a "Business Process" idea flow exists (the publish flow's Step 2 default);
  - the category tree has at least one active, non-"Other" node;
  - the application inventory is readable.

`--require-non-admin` additionally insists the identity is NOT an AH admin, for
tasks that exercise the "applications 403 → publish anyway" fallback — an admin
would create the applications instead and the regression would go untested.

`--require-new-applications` / `--require-no-new-applications` insists the Business
Process schema does / does NOT offer `new_applications` (the section's "add new
applications" control), and each
`--require-app NAME` / `--require-no-app NAME` insists the inventory does / does not
hold an application of that name. All three are tenant configuration a scenario depends on: when they drift, the run is an
environment ERROR, never a skill FAILURE.

Writes `ah-preflight.json` (tenant url, owner email, flow id, archive target, and a
snapshot of the inventory and the category tree) for seed_publish.py and the
graders, which grade against the tenant as it was when the run started. Mirrors uipath-maestro-case's preflight: a revoked
login or an asleep tenant must never be scored against the skill.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

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
# Any of these can submit a process; the two admin roles are what a tenant's
# account owner holds on a fresh tenant (observed on the alpha eval tenant).
ADMIN_ROLES = {"ah-system-admin", "ah-account-owner"}
SUBMITTER_ROLES = {"ah-standard-user", "ah-authorized-user"} | ADMIN_ROLES


def schema_offers_new_applications(flow_id) -> bool:
    """Whether the flow's schema lets a submission create applications by name.

    Decides what the applications grader may expect: with `new_applications`
    every PDD system should end up attached; without it only the ones the
    inventory already holds. Read-only — the schema is written to a temp file.
    """
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "schema.json")
        result = uip_json(["ah", "automations", "schema", "get", "--source-type", "COE",
                           "--idea-flow-id", str(flow_id), "--destination", target])
        if not succeeded(result) or not os.path.exists(target):
            return False
        with open(target, encoding="utf-8") as handle:
            return '"new_applications"' in handle.read()


def all_category_ids(categories: list[dict]) -> list[int]:
    found: list[int] = []
    for category in categories or []:
        found.append(category["CategoryId"])
        found.extend(all_category_ids(category.get("Subcategories") or []))
    return found


def main(argv: list[str]) -> int:
    require_non_admin = "--require-non-admin" in argv
    require_new_applications = "--require-new-applications" in argv
    require_no_new_applications = "--require-no-new-applications" in argv
    required_apps = [argv[i + 1] for i, arg in enumerate(argv[:-1]) if arg == "--require-app"]
    absent_apps = [argv[i + 1] for i, arg in enumerate(argv[:-1]) if arg == "--require-no-app"]
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
    if require_non_admin and (user.get("IsAdmin") == 1 or roles & ADMIN_ROLES):
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
    tree = (categories.get("Data") or {}).get("Categories") or [] if succeeded(categories) else []
    if succeeded(categories) and not active_categories(tree):
        problems.append("category tree has no active non-'Other' category")

    inventory = uip_json(["ah", "applications", "list", "--limit", "200"])
    if not succeeded(inventory):
        problems.append(f"uip ah applications list failed: {describe_failure(inventory)}")
    else:
        names = {str(a.get("Name", "")).strip().lower() for a in items(inventory)}
        problems.extend(f"inventory has no {app!r} application, which this scenario relies on"
                        for app in required_apps if app.strip().lower() not in names)
        problems.extend(f"inventory already has {app!r}, which this scenario needs to be missing"
                        for app in absent_apps if app.strip().lower() in names)

    offered = schema_offers_new_applications(flow["Id"]) if flow else False
    if require_new_applications and not offered:
        problems.append("the Business Process schema does not offer new_applications, but this scenario needs "
                        "the section's 'add new applications' control turned on")
    if require_no_new_applications and offered:
        problems.append("the Business Process schema offers new_applications, but this scenario needs "
                        "the section's 'add new applications' control turned off")

    if problems:
        print("preflight_ah: ENVIRONMENT gap — this tenant/identity cannot take a publish:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    archive = archive_target(flow) if flow else None
    summary = {
        "new_applications_offered": offered,
        "tenant_url": tenant.get("Url"),
        "owner_email": user.get("Email"),
        "is_admin": bool(user.get("IsAdmin") == 1 or roles & ADMIN_ROLES),
        "business_process_flow_id": flow.get("Id") if flow else None,
        "archive_phase": archive[0] if archive else None,
        "archive_status": archive[1] if archive else None,
        "inventory": [{"Id": a.get("Id"), "Name": a.get("Name"), "Version": a.get("Version")}
                      for a in items(inventory)],
        "active_category_ids": sorted(c["CategoryId"] for c in active_categories(tree)),
        "category_ids": sorted(all_category_ids(tree)),
    }
    with open(OUTPUT, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=1)
    print(f"preflight_ah: OK — flow {summary['business_process_flow_id']} on {summary['tenant_url']}, "
          f"{len(summary['inventory'])} inventory applications"
          + ("" if archive else "; WARNING: no Archived status on the flow, cleanup will be a no-op"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
