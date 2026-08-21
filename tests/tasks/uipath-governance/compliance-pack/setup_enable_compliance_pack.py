#!/usr/bin/env python3
"""Precondition setup for the ISO 42001 compliance-pack DISABLE test.

The disable task's prompt asserts the standard "is currently applied", and its
core criterion requires the agent to call `state disable`. But the shared test
tenant is mutable: the compliance-pack cleanup (post_run) DISABLES the pack, so
by the time the disable task runs the pack is often already inactive. A correct
agent that checks state first (which the skill teaches) then sees `Active: false`
and rightly refuses to disable a no-op — failing the test through no fault of
its own.

This script guarantees the premise: it ENABLES `iso-42001-2023` on the login
tenant so `state disable` is always the required, meaningful next step. It is the
mirror of cleanup_compliance_pack.py's `disable_pack()`.

On a successful enable it drops an ownership marker in the task sandbox;
cleanup_compliance_pack.py disables the pack only when that marker is present,
so a task never disables a pack a concurrent task is relying on.

Always exits 0 — setup failures never gate a task's pass/fail. Without live auth
every CLI call fails and the script logs + exits cleanly, so local runs (where
the CLI is not connected) are unaffected: the pack simply is not enabled and the
task grades as it would have anyway.
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="setup_enable_compliance_pack: %(message)s")
logger = logging.getLogger(__name__)

PACK_ID = "iso-42001-2023"

# Ownership marker: written ONLY when THIS run enabled the pack, so the paired
# cleanup disables only its own change. Lives in the task sandbox (cwd), not
# /tmp — pre_run/post_run execute in the shared orchestrator container, so a
# fixed /tmp path would be read and deleted by every concurrent task.
MARKER = Path(os.getcwd()) / ".iso42001-enabled-by-setup"


def run_cli(args, timeout=30):
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning("CLI exit %d for `uip %s`: %s", result.returncode,
                           " ".join(args),
                           (result.stderr or result.stdout).strip()[:300])
            return None
        return json.loads(result.stdout)
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as e:
        logger.warning("CLI call `uip %s` failed: %s", " ".join(args), e)
        return None


def get_tenant_id():
    # 1. Explicit env vars (set in CI configurations)
    for var in ("UIPATH_CLI_TENANT_ID", "UIPATH_TENANT_ID"):
        val = os.environ.get(var, "").strip()
        if val:
            logger.info("Tenant ID from %s", var)
            return val

    # 2. Auth file — Docker mount point (/.uipath/.auth) and default user path
    for auth_file in ("/.uipath/.auth", os.path.expanduser("~/.uipath/.auth")):
        if os.path.exists(auth_file):
            with open(auth_file) as f:
                for line in f:
                    if line.startswith("UIPATH_TENANT_ID="):
                        val = line.split("=", 1)[1].strip()
                        if val:
                            logger.info("Tenant ID from auth file %s", auth_file)
                            return val

    # 3. Last resort: ask uip itself
    result = run_cli(["login", "status"])
    if result and result.get("Result") == "Success":
        data = result.get("Data") or {}
        tenant_id = data.get("TenantId") or data.get("tenantId")
        if tenant_id:
            logger.info("Tenant ID from uip login status")
            return tenant_id
    return None


def enable_pack():
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("No tenant ID found — skipping pack enable (local/no-auth run)")
        return

    state = run_cli(["gov", "compliance-packs", "state", "get", "tenant", tenant_id, PACK_ID])
    data = (state or {}).get("Data") or {}
    if data.get("Active") or data.get("active"):
        logger.info("Pack %s already active on tenant %s — precondition satisfied", PACK_ID, tenant_id)
        return

    logger.info("Pack %s not active on tenant %s — enabling to establish precondition", PACK_ID, tenant_id)
    result = run_cli(["gov", "compliance-packs", "state", "enable", "tenant", tenant_id, PACK_ID])
    if result and result.get("Result") == "Success":
        MARKER.touch()
        logger.info("Pack enabled (ownership marker %s)", MARKER)
    else:
        logger.warning("Pack enable returned unexpected result: %s", result)


def main():
    logger.info("=== Compliance-pack enable setup start (pack=%s) ===", PACK_ID)
    enable_pack()
    logger.info("=== Enable setup done ===")


main()
sys.exit(0)
