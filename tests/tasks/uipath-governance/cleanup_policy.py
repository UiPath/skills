#!/usr/bin/env python3
"""Best-effort cleanup for governance policy lifecycle tests.

Deletes every policy whose name starts with the prefix the test created (this
catches both the base name and the `-renamed` variant the update step produces).
Both the policy kind and the name prefix are supplied by the calling test via
environment variables — nothing is hardcoded:

  CLEANUP_POLICY_KIND  access-policy | aops-policy
  CLEANUP_POLICY_NAME  name prefix, e.g. "lifecycle-test-access-policy"

The agent's own `delete` step is the primary cleanup; this post_run is a safety
net so a run that fails mid-flow never leaves an orphan policy on the tenant.
Always exits 0 — failures here never affect pass/fail.

The two kinds have different list/delete shapes:
  access-policy  list -> Data.Results[], id field "Id",         delete <Id>
  aops-policy    list -> Data.Result[],  id field "Identifier", delete <Identifier>
"""

import json
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_policy: %(message)s")
logger = logging.getLogger(__name__)

# kind -> (list rows key under Data, id field on each row)
KINDS = {
    "access-policy": ("Results", "Id"),
    "aops-policy": ("Result", "Identifier"),
}


def run_cli(args, timeout=30):
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning("CLI exit %d: %s", result.returncode, (result.stderr or result.stdout).strip()[:200])
            return None
        return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as e:
        logger.warning("CLI call failed: %s", e)
        return None


def main():
    kind = (os.environ.get("CLEANUP_POLICY_KIND") or "").strip()
    name_prefix = (os.environ.get("CLEANUP_POLICY_NAME") or "").strip()
    if kind not in KINDS or not name_prefix:
        logger.warning(
            "CLEANUP_POLICY_KIND (%r) must be one of %s and CLEANUP_POLICY_NAME must be set — skipping cleanup",
            kind, list(KINDS),
        )
        return

    rows_key, id_field = KINDS[kind]

    # The list endpoint caps page size (access-policy rejects --limit > 20), so
    # page through with --offset until we've seen TotalCount rows.
    page = 20
    offset = 0
    all_rows = []
    while offset <= 1000:
        data = run_cli(["gov", kind, "list", "--limit", str(page), "--offset", str(offset)])
        if not data or data.get("Result") != "Success":
            if offset == 0:
                logger.warning("Could not list %s — skipping cleanup", kind)
                return
            break  # partial list is fine for best-effort cleanup
        payload = data.get("Data") or {}
        rows = payload.get(rows_key, []) or []
        all_rows.extend(rows)
        total = payload.get("TotalCount", len(all_rows))
        offset += page
        if not rows or offset >= total:
            break

    matches = [r for r in all_rows if (r.get("Name") or "").startswith(name_prefix)]
    if not matches:
        logger.info("No %s policy starting with '%s' — nothing to clean up", kind, name_prefix)
        return

    for policy in matches:
        pid = policy.get(id_field)
        if not pid:
            continue
        logger.info("Deleting %s '%s' (%s=%s)", kind, policy.get("Name"), id_field, pid)
        result = run_cli(["gov", kind, "delete", pid])
        if result:
            logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
        else:
            logger.warning("Delete call returned no result for %s=%s", id_field, pid)


main()
sys.exit(0)
