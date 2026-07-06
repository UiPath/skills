#!/usr/bin/env python3
"""Best-effort cleanup: disable ISO 42001 pack on the test tenant after a live e2e run.

Only disables if the pack is currently active — skips silently if it was
already inactive or never enabled. Always exits 0 so cleanup failures never
affect the test pass/fail result.
"""

import json
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_compliance_pack: %(message)s")
logger = logging.getLogger(__name__)

PACK_ID = "iso-42001-2023"


def run_cli(args: list[str], timeout: int = 30) -> dict | None:
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning("CLI exit %d: %s", result.returncode,
                           result.stderr.strip() or result.stdout.strip())
            return None
        return json.loads(result.stdout)
    except Exception as e:
        logger.warning("CLI call failed: %s", e)
        return None


def get_tenant_id() -> str | None:
    # 1. Explicit env vars (set in some CI configurations)
    for var in ("UIPATH_CLI_TENANT_ID", "UIPATH_TENANT_ID"):
        val = os.environ.get(var, "").strip()
        if val:
            return val

    # 2. Auth file — check both the Docker mount point (/.uipath/.auth)
    #    and the default user path (~/.uipath/.auth)
    for auth_file in ("/.uipath/.auth", os.path.expanduser("~/.uipath/.auth")):
        if os.path.exists(auth_file):
            with open(auth_file) as f:
                for line in f:
                    if line.startswith("UIPATH_TENANT_ID="):
                        val = line.split("=", 1)[1].strip()
                        if val:
                            return val

    # 3. Last resort: ask uip itself — works whenever the CLI is authenticated
    #    regardless of how auth was set up (env vars, auth file, or ROPC token)
    result = run_cli(["login", "status"])
    if result and result.get("Result") == "Success":
        data = result.get("Data") or {}
        tenant_id = data.get("TenantId") or data.get("tenantId")
        if tenant_id:
            logger.info("Resolved tenant ID from uip login status: %s", tenant_id)
            return tenant_id

    return None


def main():
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("No tenant ID found — skipping cleanup")
        return

    # Check if the pack is currently active
    state = run_cli(["gov", "compliance-packs", "state", "get", "tenant", tenant_id, PACK_ID])
    if state is None:
        logger.info("state get returned no result (pack likely not enabled) — skipping")
        return

    active = (state.get("Data") or {}).get("Active") or \
             (state.get("Data") or {}).get("active")

    if not active:
        logger.info("Pack %s is not active on tenant %s — nothing to clean up", PACK_ID, tenant_id)
        return

    # Pack is active — disable it
    logger.info("Disabling %s on tenant %s", PACK_ID, tenant_id)
    result = run_cli(["gov", "compliance-packs", "state", "disable", "tenant", tenant_id, PACK_ID])
    if result and result.get("Result") == "Success":
        logger.info("Disabled successfully")
    else:
        logger.warning("Disable returned unexpected result: %s", result)


main()
sys.exit(0)
