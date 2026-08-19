#!/usr/bin/env python3
"""Focused cleanup for compliance-pack tests on the shared test tenant.

Compliance-pack smoke/e2e tasks run with live CLI auth in CI (smoke.yaml /
nightly.yaml pass UIPATH_CLI_* env auth into every sandbox), so flows the task
prompts assume will dead-end on auth errors actually mutate the real tenant.
This script undoes ONLY what the compliance-pack tests create:

  0. Reads the available packIds from `catalog list`. Several standards ship
     (ISO 42001, ISO 27001, …), and a task can enable any of them, so the pack
     set is discovered rather than hardcoded — a newly added standard is cleaned
     up without editing this file.
  1. Disables each of those compliance pack states on the login tenant (what the
     full-apply / `state enable` tasks turn on). Packs that are not active are
     skipped silently.
  2. Deletes AOps policies whose name starts with one of those packIds (the
     deterministic `<packId>-<clause>-<product>` namespace the partial-apply
     flow creates — see partial-apply/impl.md). Scoped by the FULL packId, never
     a loose `iso-` prefix, so it never touches human-named production policies.

It does NOT touch policies outside a compliance-pack namespace — e.g. the AOps
"Block ChatGPT" routing tests create their own named policy and are cleaned up
by cleanup_policy.py keyed to that exact name.

After deleting, it re-lists and logs the surviving pack-namespaced policies plus
the tenant-wide policy count, so a CI run's log alone confirms cleanup worked.

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

# Pack IDs come from `catalog list` at runtime — more than one standard ships now, and
# hardcoding ids means a newly added standard's leftovers survive cleanup on the shared
# tenant. Partial apply names its policies `<packId>-<scope>-<product>`, so each packId
# is also its policy-name namespace. This constant is only the fallback for when the
# catalog cannot be read (no auth / no connectivity).
FALLBACK_PACK_IDS = ["iso-42001-2023", "iso-27001-2022"]


def pack_ids():
    catalog = run_cli(["gov", "compliance-packs", "catalog", "list"])
    payload = (catalog or {}).get("Data") or {}
    packs = payload.get("Packs") or payload.get("packs") or []
    ids = [p.get("PackId") or p.get("packId") for p in packs]
    ids = [i for i in ids if i]
    if not ids:
        logger.warning("Could not read pack catalog — falling back to %s", FALLBACK_PACK_IDS)
        return FALLBACK_PACK_IDS
    return ids


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


def disable_packs(packs):
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("No tenant ID found — skipping pack disable")
        return

    for pack_id in packs:
        state = run_cli(["gov", "compliance-packs", "state", "get", "tenant", tenant_id, pack_id])
        if state is None:
            logger.info("state get returned no result for %s (pack likely not enabled) — skipping disable",
                        pack_id)
            continue

        data = state.get("Data") or {}
        if not (data.get("Active") or data.get("active")):
            logger.info("Pack %s not active on tenant %s — nothing to disable", pack_id, tenant_id)
            continue

        logger.info("Pack %s IS active on tenant %s — disabling", pack_id, tenant_id)
        result = run_cli(["gov", "compliance-packs", "state", "disable", "tenant", tenant_id, pack_id])
        if result and result.get("Result") == "Success":
            logger.info("Pack %s disabled", pack_id)
        else:
            logger.warning("Pack %s disable returned unexpected result: %s", pack_id, result)


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


def pack_policies(rows, packs):
    # Partial apply names policies `<packId>-<scope>-<product>`, so the packId is the prefix.
    # Match on the full packId, never a loose `iso-` — that would sweep up a tenant's own policies.
    prefixes = tuple(p.lower() for p in packs)
    return [r for r in rows if (r.get("Name") or "").lower().startswith(prefixes)]


def main():
    packs = pack_ids()
    logger.info("=== Compliance-pack cleanup start (packs=%s) ===", ", ".join(packs))

    disable_packs(packs)

    rows = list_policies()
    if rows is None:
        logger.warning("Could not list aops-policy (no auth / no connectivity) — nothing deleted")
        return

    matches = pack_policies(rows, packs)
    logger.info("Tenant has %d AOps policies; %d in a compliance-pack namespace", len(rows), len(matches))
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
        surviving = pack_policies(final_rows, packs)
        remaining = len(surviving)
        logger.info("=== Post-cleanup tenant state ===")
        logger.info("Tenant now has %d AOps policies total; %d still in a compliance-pack namespace",
                    len(final_rows), remaining)
        for r in surviving:
            logger.warning("  STILL PRESENT: %-60s Identifier=%s",
                           r.get("Name", "?"), r.get("Identifier", "?"))

    logger.info("=== Cleanup done: %d matched, %d deleted, %d failed, %s remaining ===",
                len(matches), deleted, len(failed), remaining)


main()
sys.exit(0)
