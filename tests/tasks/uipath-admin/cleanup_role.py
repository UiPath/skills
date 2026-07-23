#!/usr/bin/env python3
"""Best-effort cleanup: delete every Custom role whose name matches the one the
test created. The role name is supplied by the calling test via the
CLEANUP_ROLE_NAME environment variable — nothing is hardcoded here, so this
script is shared across all authz role-lifecycle tests.

The agent's own `roles delete` step should remove the role; this post_run is a
safety net so a failed or incomplete run never leaves an orphan role on the
tenant. Always exits 0 — failures here never affect pass/fail.

Note: `roles list` nests its rows under Data.Results (not a flat Data list like
`pat list`), so this script does not reuse admin_helpers.find_all.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli

logging.basicConfig(level=logging.INFO, format="cleanup_role: %(message)s")
logger = logging.getLogger(__name__)


def main():
    role_name = (os.environ.get("CLEANUP_ROLE_NAME") or "").strip()
    if not role_name:
        logger.warning("CLEANUP_ROLE_NAME not set — skipping cleanup")
        return

    data = run_cli([
        "admin", "authorization", "roles", "list",
        "--role-type", "Custom", "--filter", role_name,
    ])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list roles — skipping cleanup")
        return

    # `roles list` returns Data = {TotalCount, Results}; tolerate a flat list too.
    payload = data.get("Data") or {}
    results = payload.get("Results", payload) if isinstance(payload, dict) else payload
    matches = [
        r for r in results
        if (r.get("Name") or r.get("name")) == role_name
        and (r.get("Type") or r.get("type")) == "Custom"
    ]
    if not matches:
        logger.info("No '%s' role found — nothing to clean up", role_name)
        return

    for role in matches:
        role_id = role.get("Id") or role.get("id")
        if not role_id:
            continue
        logger.info("Deleting role '%s' (id=%s)", role_name, role_id)
        result = run_cli(["admin", "authorization", "roles", "delete", role_id])
        if result:
            logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
        else:
            logger.warning("Delete call returned no result for id=%s", role_id)


main()
sys.exit(0)
