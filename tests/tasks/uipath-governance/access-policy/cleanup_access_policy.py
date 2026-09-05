#!/usr/bin/env python3
"""Post-run cleanup for the access-policy suite — this run's policies only.

Deletes every access policy whose name carries this run's id, plus any id
recorded in seed.json (which covers a policy the agent renamed). Policies
belonging to a concurrently executing run keep a different id suffix and are
never touched, so several agents can run the same task against one organization.

Two things make this robust rather than merely best-effort:

  * The listing read is retried. The access-policy service returns HTTP 503
    intermittently, and a single failed read would otherwise leak every object
    this run created.
  * Marker policies older than GOV_STALE_HOURS (default 6) are swept regardless
    of which run owns them, which reclaims leaks from runs that were killed or
    that hit an outage. A concurrently executing run's policies are minutes old,
    so the age floor cannot touch them.

Always exits 0 — cleanup never decides pass/fail.
"""

import logging
import os
import sys
from datetime import datetime, timedelta, timezone

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-governance", "_shared")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_shared')
)
sys.path.insert(0, _shared_root)
from gov_helpers import ap_delete, ap_live_rows, load_seed, owned_by_this_run, poll

logging.basicConfig(level=logging.INFO, format="cleanup_access_policy: %(message)s")
logger = logging.getLogger(__name__)

MARKER_PREFIX = "ce-gov"


def stale(row: dict, hours: float) -> bool:
    """True when a marker policy is old enough that no live run can own it."""
    if not str(row.get("Name") or "").startswith(MARKER_PREFIX):
        return False
    stamp = str(row.get("CreatedOn") or "")
    if not stamp:
        return False
    try:
        created = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (datetime.now(timezone.utc) - created) > timedelta(hours=hours)


def main():
    seed = load_seed()
    token = seed.get("uuid8")

    try:
        hours = float(os.environ.get("GOV_STALE_HOURS") or 6)
    except ValueError:
        hours = 6.0

    rows = poll(ap_live_rows, max_attempts=3, delay=5) or []
    if not rows:
        logger.warning("Could not read the policy list — this run's objects may be left behind")

    removed = set()
    for row in rows:
        if stale(row, hours):
            pid = row.get("Id")
            if pid and ap_delete(pid):
                removed.add(pid)
                logger.info("Swept stale marker policy '%s' (%s)", row.get("Name"), pid)

    if not token:
        logger.info("No seed.json in the run directory — nothing owned by this run")
        logger.info("Removed %d stale policy/policies", len(removed))
        return

    for row in rows:
        name = row.get("Name") or ""
        pid = row.get("Id")
        if pid and pid not in removed and owned_by_this_run(name):
            if ap_delete(pid):
                removed.add(pid)
                logger.info("Deleted '%s' (%s)", name, pid)

    for key, entry in seed.items():
        if isinstance(entry, dict) and entry.get("id") and entry["id"] not in removed:
            if ap_delete(entry["id"]):
                removed.add(entry["id"])
                logger.info("Deleted policy recorded under seed key '%s' (%s)", key, entry["id"])

    logger.info("Run %s: removed %d policy/policies", token, len(removed))


main()
sys.exit(0)
