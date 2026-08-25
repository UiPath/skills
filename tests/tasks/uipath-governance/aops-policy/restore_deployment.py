#!/usr/bin/env python3
"""Post-run for deployment scenarios: put the caller's user and the tenant back to their snapshots,
remove this run's marker group, then delete this run's policies.

Order matters: `aops-policy delete` is refused while a policy is still assigned, so assignments are
restored first and the policy cleanup (cleanup_aops_policy.py, same helpers) runs last.

`deployment <subject> configure` is a FULL REPLACE, so re-sending the snapshot array is exactly the
pre-run state. Always exits 0 — cleanup never decides pass/fail.
"""

import json
import logging
import os
import runpy
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared'))
from gov_helpers import load_seed, owned_by_this_run, run_cli, run_id

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


def main():
    seed = load_seed()
    dep = seed.get("deployment") or {}

    if "user_snapshot" in dep and dep.get("userId"):
        extra = ["--user", dep.get("userName") or dep["userId"]]
        if dep.get("userEmail"):
            extra += ["--email", dep["userEmail"]]
        if dep.get("userSource"):
            extra += ["--source", dep["userSource"]]
        ok = configure("user", dep["userId"], dep["user_snapshot"], extra)
        logger.info("user %s restored to %d pin(s): %s", dep["userId"], len(dep["user_snapshot"]), ok)

    if "tenant_snapshot" in dep and dep.get("tenantId"):
        ok = configure("tenant", dep["tenantId"], dep["tenant_snapshot"], ["--tenant-name", dep.get("tenantName") or ""])
        logger.info("tenant %s restored to %d assignment(s): %s", dep["tenantId"], len(dep["tenant_snapshot"]), ok)

    subjects = seed.get("subjects") or {}
    gid, gname = subjects.get("groupId"), subjects.get("groupName")
    if gid and gname and owned_by_this_run(gname):
        run_cli(["gov", "aops-policy", "deployment", "group", "delete", gid])
        res = run_cli(["admin", "groups", "delete", gid])
        logger.info("marker group '%s' removed from governance and directory: %s", gname, bool(res))

    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cleanup_aops_policy.py"))


main()
sys.exit(0)
