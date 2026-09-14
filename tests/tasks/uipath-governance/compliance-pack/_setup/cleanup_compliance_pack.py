#!/usr/bin/env python3
"""Focused cleanup for ISO 42001 compliance-pack tests on the shared test tenant.

Compliance-pack smoke/e2e tasks run with live CLI auth in CI (smoke.yaml /
nightly.yaml pass UIPATH_CLI_* env auth into every sandbox), so flows the task
prompts assume will dead-end on auth errors actually mutate the real tenant.
This script undoes ONLY what the compliance-pack tests create:

  1. Disables the `iso-42001-2023` compliance pack state on the login tenant
     (what the full-apply / `state enable` tasks turn on). Skipped silently if
     the pack is not active.
  2. Deletes AOps policies whose name starts with `iso-42001` (the deterministic
     `iso-42001-2023-<clause>-<product>` namespace the partial-apply flow
     creates — see partial-apply/impl.md). Scoped by that prefix so it never
     touches human-named production policies on the tenant.

It does NOT touch policies outside the ISO 42001 namespace — e.g. the AOps
"Block ChatGPT" routing tests create their own named policy and are cleaned up
by cleanup_policy.py keyed to that exact name.

After deleting, it re-lists and logs the surviving `iso-42001` policies plus the
tenant-wide policy count, so a CI run's log alone confirms the cleanup worked.

Known limitation: `aops-policy delete` is blocked while a policy is still
referenced by a deployment assignment. Observed debris is all UNDEPLOYED, so a
plain delete clears it; a blocked delete is logged and shows up in the surviving
count rather than silently passing.

Always exits 0 — cleanup failures never affect a task's pass/fail result.
Without live auth every CLI call fails, and the script logs + exits cleanly, so
local runs are unaffected.
"""

import json
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_compliance_pack: %(message)s")
logger = logging.getLogger(__name__)

PACK_ID = "iso-42001-2023"
POLICY_NAME_PREFIX = "iso-42001"  # compliance-pack partial-apply namespace


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


def disable_pack():
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("No tenant ID found — skipping pack disable")
        return

    state = run_cli(["gov", "compliance-packs", "state", "get", "tenant", tenant_id, PACK_ID])
    if state is None:
        logger.info("state get returned no result (pack likely not enabled) — skipping disable")
        return

    data = state.get("Data") or {}
    if not (data.get("Active") or data.get("active")):
        logger.info("Pack %s not active on tenant %s — nothing to disable", PACK_ID, tenant_id)
        return

    logger.info("Pack %s IS active on tenant %s — disabling", PACK_ID, tenant_id)
    result = run_cli(["gov", "compliance-packs", "state", "disable", "tenant", tenant_id, PACK_ID])
    if result and result.get("Result") == "Success":
        logger.info("Pack disabled")
    else:
        logger.warning("Pack disable returned unexpected result: %s", result)


def list_policies():
    """Page through aops-policy list. Returns all rows, or None if listing failed.

    NOTE: for `aops-policy list` the CLI's --offset is a PAGE INDEX, not a row
    offset (verified against the live service: --limit 20 --offset 1 returns
    rows 21-40, --offset 20 returns nothing). Dedupe by Identifier guards
    against overlap if the semantics ever change.
    """
    page = 20
    page_index = 0
    all_rows = []
    seen = set()
    while page_index <= 200:
        data = run_cli(["gov", "aops-policy", "list", "--limit", str(page), "--offset", str(page_index)])
        if not data or data.get("Result") != "Success":
            if page_index == 0:
                return None
            logger.warning("List page %d failed — proceeding with %d rows collected",
                           page_index, len(all_rows))
            break  # partial list is fine for best-effort cleanup
        payload = data.get("Data") or {}
        rows = payload.get("Result", []) or []
        new_rows = [r for r in rows if r.get("Identifier") not in seen]
        seen.update(r.get("Identifier") for r in new_rows)
        all_rows.extend(new_rows)
        total = payload.get("TotalCount", len(all_rows))
        page_index += 1
        if not rows or not new_rows or len(all_rows) >= total:
            break
    return all_rows


def iso_policies(rows):
    return [r for r in rows if (r.get("Name") or "").lower().startswith(POLICY_NAME_PREFIX)]


def main():
    logger.info("=== Compliance-pack cleanup start (pack=%s, policy prefix=%s) ===",
                PACK_ID, POLICY_NAME_PREFIX)

    disable_pack()

    rows = list_policies()
    if rows is None:
        logger.warning("Could not list aops-policy (no auth / no connectivity) — nothing deleted")
        return

    matches = iso_policies(rows)
    logger.info("Tenant has %d AOps policies; %d in the ISO 42001 namespace", len(rows), len(matches))
    for r in matches:
        logger.info("  matched: %-60s Identifier=%s Priority=%s",
                    r.get("Name", "?"), r.get("Identifier", "?"), r.get("Priority", "?"))

    deleted = 0
    failed = []
    for policy in matches:
        pid = policy.get("Identifier")
        name = policy.get("Name", "?")
        if not pid:
            logger.warning("SKIP (no Identifier on row): %s", name)
            failed.append(name)
            continue
        result = run_cli(["gov", "aops-policy", "delete", pid])
        if result and result.get("Result") == "Success":
            logger.info("  deleted: %s (%s)", name, pid)
            deleted += 1
        else:
            logger.warning("  DELETE FAILED (may be deployment-assigned): %s (%s) -> %s",
                           name, pid, result)
            failed.append(name)

    # Final validation pass: re-list and report what survived.
    final_rows = list_policies()
    if final_rows is None:
        logger.warning("Final validation list failed — cannot confirm surviving count")
        remaining = "?"
    else:
        surviving = iso_policies(final_rows)
        remaining = len(surviving)
        logger.info("=== Post-cleanup tenant state ===")
        logger.info("Tenant now has %d AOps policies total; %d still in the ISO 42001 namespace",
                    len(final_rows), remaining)
        for r in surviving:
            logger.warning("  STILL PRESENT: %-60s Identifier=%s",
                           r.get("Name", "?"), r.get("Identifier", "?"))

    logger.info("=== Cleanup done: %d matched, %d deleted, %d failed, %s remaining ===",
                len(matches), deleted, len(failed), remaining)


main()
sys.exit(0)
