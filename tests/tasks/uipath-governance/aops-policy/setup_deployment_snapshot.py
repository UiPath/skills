#!/usr/bin/env python3
"""Pre-run for deployment scenarios: snapshot the subject's assignments so post_run can restore them.

  AOPS_SNAPSHOT_SCOPES  comma list of user,tenant — scopes to snapshot (default "user,tenant")
  AOPS_GROUP_BASE       create a marker directory group (name gets this run's id) — the group scope
                        subject; a brand-new group has no members, so pinning to it governs nobody
  AOPS_PIN_GROUP_KEY    seed.json key of an already-seeded policy to pin on that marker group for
                        product E2E (precedence scenarios: a narrower-scope override must pre-exist)

Writes `seed.json["deployment"]` = {userId, userName, userEmail, userSource, tenantId, tenantName,
user_snapshot: [...], tenant_snapshot: [...]} plus `seed.json["subjects"]` for the marker group.
Snapshots are the exact `--input` arrays `deployment <subject> configure` takes.

Only the caller's own user, this run's marker group and the shared E2E test product are ever touched.
Always exits 0 — a failed snapshot leaves the key absent, so the scenario's own check fails rather
than passing for free.
"""

import json
import logging
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from gov_helpers import login_info, run_cli, run_id, scoped, seed_entry, subject_policies, tenant_policies, update_seed

logging.basicConfig(level=logging.INFO, format="setup_deployment_snapshot: %(message)s")
logger = logging.getLogger(__name__)

PRODUCT = "E2E"


def own_user_pins(entries: list[dict]) -> list[dict]:
    """Entries pinned directly on the user: a real PolicyIdentifier and no group provenance.

    `deployment user get` also lists every product with PolicyIdentifier null (nothing pinned) and
    group-inherited rows (GroupName set) — neither is a user pin.
    """
    pins = []
    for e in entries:
        pid = e.get("PolicyIdentifier") or e.get("policyIdentifier")
        if not pid or e.get("GroupName") or e.get("groupName"):
            continue
        pins.append({"productIdentifier": e.get("ProductIdentifier") or e.get("productIdentifier"),
                     "policyIdentifier": pid})
    return pins


def tenant_pins(entries: list[dict]) -> list[dict]:
    return [{"productIdentifier": e.get("ProductIdentifier") or e.get("productIdentifier"),
             "licenseTypeIdentifier": e.get("LicenseTypeIdentifier") or e.get("licenseTypeIdentifier"),
             "policyIdentifier": e.get("PolicyIdentifier") if "PolicyIdentifier" in e else e.get("policyIdentifier")}
            for e in entries]


def user_source(user_id: str) -> str | None:
    data = run_cli(["gov", "aops-policy", "deployment", "user", "list", "--limit", "100"])
    for row in (((data or {}).get("Data") or {}).get("Result") or []):
        if row.get("Identifier") == user_id:
            return row.get("Source")
    return None


def configure_group(group_id: str, group_name: str, entries: list[dict]) -> bool:
    path = os.path.join(tempfile.gettempdir(), f"aops-group-pin-{run_id()}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(entries, fh)
    data = run_cli(["gov", "aops-policy", "deployment", "group", "configure", group_id,
                    "--group", group_name, "--input", path], timeout=120)
    try:
        os.remove(path)
    except OSError:
        pass
    return bool(data and data.get("Result") == "Success")


def main():
    scopes = {s.strip() for s in (os.environ.get("AOPS_SNAPSHOT_SCOPES") or "user,tenant").split(",") if s.strip()}
    me = login_info()
    if not me.get("UserId") or not me.get("TenantId"):
        logger.warning("Could not read UserId/TenantId from `uip login status` — nothing snapshotted")
        return
    dep = {"userId": me["UserId"], "userName": me.get("UserName") or me.get("UserEmail") or me["UserId"],
           "userEmail": me.get("UserEmail") or "", "userSource": user_source(me["UserId"]) or "",
           "tenantId": me["TenantId"], "tenantName": me.get("Tenant") or ""}

    if "user" in scopes:
        entries = subject_policies("user", dep["userId"])
        if entries is None:
            logger.warning("deployment user get failed — user scope not snapshotted")
        else:
            dep["user_snapshot"] = own_user_pins(entries)
            logger.info("user %s has %d own pin(s)", dep["userId"], len(dep["user_snapshot"]))
    if "tenant" in scopes:
        entries = tenant_policies(dep["tenantId"])
        if entries is None:
            logger.warning("deployment tenant get failed — tenant scope not snapshotted")
        else:
            dep["tenant_snapshot"] = tenant_pins(entries)
            logger.info("tenant %s has %d assignment(s)", dep["tenantId"], len(dep["tenant_snapshot"]))
    update_seed(deployment=dep)

    group_base = (os.environ.get("AOPS_GROUP_BASE") or "").strip()
    gid = gname = None
    if group_base:
        gname = scoped(group_base)
        res = run_cli(["admin", "groups", "create", gname])
        if res and res.get("Result") == "Success":
            data = run_cli(["admin", "groups", "list"])
            for row in ((data or {}).get("Data") or []):
                if (row.get("Name") or row.get("name") or "") == gname:
                    gid = row.get("Id") or row.get("id")
        if gid:
            update_seed(subjects={"groupName": gname, "groupId": gid})
            logger.info("Run %s created marker group '%s' (%s)", run_id(), gname, gid)
        else:
            logger.warning("Could not create marker group '%s': %s", gname, res)

    pin_key = (os.environ.get("AOPS_PIN_GROUP_KEY") or "").strip()
    if pin_key and gid:
        entry = seed_entry(pin_key)
        if not entry or not entry.get("identifier"):
            logger.warning("seed key '%s' has no identifier — cannot pin", pin_key)
            return
        if configure_group(gid, gname, [{"productIdentifier": PRODUCT, "policyIdentifier": entry["identifier"]}]):
            logger.info("Pinned '%s' on group '%s' for product %s", entry["name"], gname, PRODUCT)
        else:
            logger.warning("group configure failed — override not pinned")


main()
sys.exit(0)
