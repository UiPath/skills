#!/usr/bin/env python3
"""Best-effort cleanup for aops-policy deployment lifecycle tests.

Clears tenant and user deployments that reference test policies so that
the subsequent cleanup_policy.py can delete the policies without being
blocked by the "deployment still references policy" guard.

  1. Removes the E2E product / E2E license-type entry from the login tenant
  2. Deletes deployments for the current login user (matched by UserName
     from login status against the governance user list)

Always exits 0 — failures here never affect pass/fail.
"""

import json
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_deployments: %(message)s")
logger = logging.getLogger(__name__)


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
    # 1. Resolve login tenant and remove E2E/E2E tenant deployment entry
    status = run_cli(["login", "status"])
    if not status or status.get("Result") != "Success":
        logger.warning("Could not get login status — skipping deployment cleanup")
        return

    tenant_id = (status.get("Data") or {}).get("TenantId")
    if tenant_id:
        logger.info("Removing E2E/E2E tenant deployment for tenant %s", tenant_id)
        run_cli(["gov", "aops-policy", "deployment", "tenant", "remove", tenant_id,
                 "--product-name", "E2E", "--license-type", "E2E"])
    else:
        logger.warning("No TenantId in login status — skipping tenant deployment cleanup")

    # 2. Delete deployments for the current login user only
    login_user = (status.get("Data") or {}).get("UserName", "")
    if not login_user:
        logger.warning("No UserName in login status — skipping user deployment cleanup")
        return

    users = run_cli(["gov", "aops-policy", "deployment", "user", "list"])
    if not users or users.get("Result") != "Success":
        logger.info("No governance users listed — skipping user deployment cleanup")
        return

    user_rows = (users.get("Data") or {}).get("Result", []) or []
    for user in user_rows:
        uid = user.get("Identifier")
        name = user.get("Name", "")
        if not uid:
            continue
        # Only delete deployments for the current login user
        if name.lower() != login_user.lower():
            continue
        logger.info("Deleting deployments for governance user %s (%s)", uid, name)
        run_cli(["gov", "aops-policy", "deployment", "user", "delete", uid])


main()
sys.exit(0)
