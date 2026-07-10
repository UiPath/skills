#!/usr/bin/env python3
"""Best-effort sweep cleanup for governance test debris on the shared test tenant.

Compliance-pack and AOps smoke tests run with live CLI auth in CI (smoke.yaml /
nightly.yaml pass UIPATH_CLI_* env auth into every sandbox), so flows the task
authors assumed would dead-end on auth errors actually create real policies
(`iso-42001-2023-<clause>-<product>`, "Block ChatGPT ...") and enable the real
ISO 42001 pack. This script deletes that debris. It is invoked from task
pre_run/post_run hooks and from the temporary tenant-sweep task.

Configuration via environment variables:

  CLEANUP_NAME_PATTERNS  comma-separated, case-insensitive SUBSTRING matches
                         against AOps policy names. Default: "iso-42001".
                         Every matching policy is deleted — safe only because
                         the test tenant holds no production policies.
  CLEANUP_DISABLE_PACK   "1" -> also disable the iso-42001-2023 compliance
                         pack state on the login tenant (skipped silently if
                         the pack is not active).
  CLEANUP_SUMMARY_FILE   optional path; when set, writes a JSON summary
                         {"patterns", "matched", "deleted", "failed",
                          "remaining", "remaining_names",
                          "tenant_policy_count"} where the remaining fields
                         are recounted from a fresh list AFTER deletion. Lets
                         a success criterion assert `"remaining": 0`
                         deterministically.

After deleting, the script ALWAYS re-lists the tenant's AOps policies and logs
what is left (matching leftovers by name, plus the tenant-wide policy count)
so a CI run's log is enough to validate the cleanup worked.

Always exits 0 — cleanup failures never affect a task's pass/fail result.
Without live auth every CLI call fails and the script logs + exits cleanly,
so local runs are unaffected.
"""

import json
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_governance_sweep: %(message)s")
logger = logging.getLogger(__name__)

PACK_ID = "iso-42001-2023"


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
    rows 21-40, --offset 20 returns nothing). `access-policy list` uses a
    row-based offset instead — do not copy this loop for that kind.
    Dedupe by Identifier guards against overlap if the semantics ever change.
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


def match(rows, patterns):
    return [r for r in rows
            if any(p in (r.get("Name") or "").lower() for p in patterns)]


def main():
    patterns = [p.strip().lower()
                for p in os.environ.get("CLEANUP_NAME_PATTERNS", "iso-42001").split(",")
                if p.strip()]
    summary_file = os.environ.get("CLEANUP_SUMMARY_FILE", "").strip()
    disable = os.environ.get("CLEANUP_DISABLE_PACK", "").strip() == "1"

    logger.info("=== Sweep start ===")
    logger.info("Patterns (case-insensitive substring): %s | disable pack: %s | summary file: %s",
                patterns, disable, summary_file or "(none)")

    if disable:
        disable_pack()

    rows = list_policies()
    if rows is None:
        logger.warning("Could not list aops-policy (no auth / no connectivity) — nothing swept")
        if summary_file:
            with open(summary_file, "w") as f:
                json.dump({"patterns": patterns, "matched": -1, "deleted": 0,
                           "failed": ["aops-policy list failed"],
                           "remaining": -1, "remaining_names": [],
                           "tenant_policy_count": -1}, f, indent=2)
        return

    matches = match(rows, patterns)
    logger.info("Tenant has %d AOps policies; %d match the sweep patterns",
                len(rows), len(matches))
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
            logger.warning("  DELETE FAILED: %s (%s) -> %s", name, pid, result)
            failed.append(name)

    # Final validation pass: re-list and report what is left on the tenant.
    final_rows = list_policies()
    if final_rows is None:
        logger.warning("Final validation list failed — cannot confirm remaining count")
        remaining_rows = None
    else:
        remaining_rows = match(final_rows, patterns)
        logger.info("=== Post-sweep tenant state ===")
        logger.info("Tenant now has %d AOps policies total; %d still match sweep patterns",
                    len(final_rows), len(remaining_rows))
        for r in remaining_rows:
            logger.warning("  STILL PRESENT: %-60s Identifier=%s",
                           r.get("Name", "?"), r.get("Identifier", "?"))

    logger.info("=== Sweep done: %d matched, %d deleted, %d failed, %s remaining ===",
                len(matches), deleted, len(failed),
                "?" if remaining_rows is None else len(remaining_rows))

    if summary_file:
        with open(summary_file, "w") as f:
            json.dump({
                "patterns": patterns,
                "matched": len(matches),
                "deleted": deleted,
                "failed": failed,
                "remaining": -1 if remaining_rows is None else len(remaining_rows),
                "remaining_names": [r.get("Name") for r in (remaining_rows or [])],
                "tenant_policy_count": -1 if final_rows is None else len(final_rows),
            }, f, indent=2)
        logger.info("Summary written to %s", summary_file)


main()
sys.exit(0)
