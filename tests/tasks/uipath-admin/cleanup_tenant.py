#!/usr/bin/env python3
"""Best-effort cleanup: soft-delete every tenant whose name carries the fixture
marker the calling test used. The marker is supplied via CLEANUP_TENANT_MARKER
so this script is shared across OMS tenant-lifecycle tests — a substring match
also catches the renamed form a test produced with `tenants update --name`.

The agent's own `tenants delete` step should retire the fixture tenant; this
post_run is a safety net so a failed or incomplete run never leaves an orphan
tenant on the organization. `tenants delete` is soft-only (Rule 19), so already
`Deleted` tenants are skipped rather than re-deleted. Always exits 0 — failures
here never affect pass/fail.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '_shared'))
from admin_helpers import run_cli, first_list

logging.basicConfig(level=logging.INFO, format="cleanup_tenant: %(message)s")
logger = logging.getLogger(__name__)


def main():
    marker = (os.environ.get("CLEANUP_TENANT_MARKER") or "").strip()
    if not marker:
        logger.warning("CLEANUP_TENANT_MARKER not set — skipping cleanup")
        return

    data = run_cli(["admin", "tenants", "list", "--filter", marker])
    if not data or data.get("Result") != "Success":
        logger.warning("Could not list tenants — skipping cleanup")
        return

    rows = first_list(data.get("Data")) or []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("Name") or row.get("name") or "")
        if marker not in name:
            continue
        status = str(row.get("Status") or row.get("status") or "")
        if status == "Deleted":
            logger.info("Tenant '%s' is already Deleted — nothing to do", name)
            continue
        tenant_id = row.get("Id") or row.get("id")
        if not tenant_id:
            continue
        logger.info("Soft-deleting tenant '%s' (id=%s, status=%s)", name, tenant_id, status)
        result = run_cli(["admin", "tenants", "delete", tenant_id])
        if result:
            logger.info("Delete result: %s — %s", result.get("Result"), result.get("Message", ""))
        else:
            logger.warning("Delete call returned no result for id=%s", tenant_id)


main()
sys.exit(0)
