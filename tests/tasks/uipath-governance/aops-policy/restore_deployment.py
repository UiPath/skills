#!/usr/bin/env python3
"""Post-run for deployment scenarios: undo this run's pins on the caller's user and the tenant,
remove this run's marker group, then delete this run's policies.

The restore is targeted, not a blind overwrite: it drops every entry that points at a policy this
run created (or that this run's seed recorded) and re-adds snapshot entries that went missing.
Several agents run the same task concurrently against one shared organization, so overwriting the
user's or tenant's whole assignment list with a stale snapshot would wipe a sibling run's pin.

Order matters: `aops-policy delete` is refused while a policy is still assigned, so assignments are
restored first and the policy cleanup (cleanup_aops_policy.py, same helpers) runs last.
Always exits 0 — cleanup never decides pass/fail.
"""

import json
import logging
import os
import runpy
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from gov_helpers import (aops_search, load_seed, owned_by_this_run, run_cli, run_id, subject_policies,
                        tenant_policies)

logging.basicConfig(level=logging.INFO, format="restore_deployment: %(message)s")
logger = logging.getLogger(__name__)


def configure(subject: str, subject_id: str, entries: list[dict], extra: list[str]) -> bool:
    path = os.path.join(tempfile.gettempdir(), f"aops-restore-{subject}-{run_id()}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(entries, fh)
    data = run_cli(["gov", "aops-policy", "deployment", subject, "configure", subject_id, *extra, "--input", path],
                   timeout=120)
    try:
        os.remove(path)
    except OSError:
        pass
    return bool(data and data.get("Result") == "Success")


def this_runs_policy_ids(seed: dict) -> set[str]:
    ids = {str(e["identifier"]).lower() for e in seed.values()
           if isinstance(e, dict) and e.get("identifier")}
    token = seed.get("uuid8")
    if token:
        for row in aops_search(token):
            if row.get("Identifier") and owned_by_this_run(row.get("Name") or ""):
                ids.add(str(row["Identifier"]).lower())
    return ids


def g(e: dict, *keys):
    return next((e[k] for k in keys if k in e), None)


def main():
    seed = load_seed()
    dep = seed.get("deployment") or {}
    ours = this_runs_policy_ids(seed)

    if "user_snapshot" in dep and dep.get("userId"):
        current = subject_policies("user", dep["userId"]) or []
        keep = [{"productIdentifier": g(e, "ProductIdentifier", "productIdentifier"),
                 "policyIdentifier": g(e, "PolicyIdentifier", "policyIdentifier")}
                for e in current
                if g(e, "PolicyIdentifier", "policyIdentifier") and not g(e, "GroupName", "groupName")
                and str(g(e, "PolicyIdentifier", "policyIdentifier")).lower() not in ours]
        have = {p["productIdentifier"] for p in keep}
        keep += [p for p in dep["user_snapshot"] if p["productIdentifier"] not in have]
        extra = ["--user", dep.get("userName") or dep["userId"]]
        if dep.get("userEmail"):
            extra += ["--email", dep["userEmail"]]
        if dep.get("userSource"):
            extra += ["--source", dep["userSource"]]
        ok = configure("user", dep["userId"], keep, extra)
        logger.info("user %s: this run's pins removed, %d pin(s) kept/restored: %s", dep["userId"], len(keep), ok)

    if "tenant_snapshot" in dep and dep.get("tenantId"):
        current = tenant_policies(dep["tenantId"]) or []
        keep = [{"productIdentifier": g(e, "ProductIdentifier", "productIdentifier"),
                 "licenseTypeIdentifier": g(e, "LicenseTypeIdentifier", "licenseTypeIdentifier"),
                 "policyIdentifier": g(e, "PolicyIdentifier", "policyIdentifier")}
                for e in current
                if str(g(e, "PolicyIdentifier", "policyIdentifier") or "").lower() not in ours]
        have = {(p["productIdentifier"], p["licenseTypeIdentifier"]) for p in keep}
        keep += [p for p in dep["tenant_snapshot"] if (p["productIdentifier"], p["licenseTypeIdentifier"]) not in have]
        ok = configure("tenant", dep["tenantId"], keep, ["--tenant-name", dep.get("tenantName") or ""])
        logger.info("tenant %s: this run's pins removed, %d assignment(s) kept/restored: %s", dep["tenantId"], len(keep), ok)

    subjects = seed.get("subjects") or {}
    gid, gname = subjects.get("groupId"), subjects.get("groupName")
    if gid and gname and owned_by_this_run(gname):
        run_cli(["gov", "aops-policy", "deployment", "group", "delete", gid])
        res = run_cli(["admin", "groups", "delete", gid])
        logger.info("marker group '%s' removed from governance and directory: %s", gname, bool(res))

    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleanup_aops_policy.py"))


main()
sys.exit(0)
