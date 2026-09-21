#!/usr/bin/env python3
"""post_run: delete the OAuth external application(s) this run minted.

Dashboard build tests that run against a live tenant mint a fresh External
Application per run via `uip admin external-apps create` (see the skill's
`dashboards/plugins/build/impl.md` Phase 3, which names it
`UiPath Dashboard - <DASHBOARD_NAME>`). Left behind, each run orphans one live
OAuth client — carrying real `OR.*` scopes — on a shared org.

**This script must never depend on the agent choosing to record the id.** An
earlier revision read only `report.json` / `.external_app_to_cleanup`, both of
which the agent had to write voluntarily. It mostly didn't: by 2026-09 the eval
org carried 924 orphaned `UiPath Dashboard - *` registrations, 145 of them from
a single task. The authoritative record is `intent.json` — the build flow writes
the minted `clientId` into it as a documented step, so scanning the sandbox for
it is deterministic and needs no prompt cooperation.

Read order (every hit is deleted, deduplicated):
  1. `intent.json` anywhere in the sandbox -> `clientId`   (authoritative)
  2. `report.json` -> `external_app_client_id` / `clientId`
  3. `.external_app_to_cleanup` marker file

Deliberately NOT done: sweeping every `UiPath Dashboard - *` app that is new
since a pre_run snapshot. Dashboard tasks run concurrently (`-j6`, plus the
claude and codex runs overlap), so a blanket sweep would delete a peer run's
app out from under it mid-build. Every source above is scoped to this task's own
sandbox, so it can only ever remove this run's app.

> **Deleting does not reclaim identity quota.** `ExternalClient` delete is a
> soft delete (`IsDeleted = true`), and the `Identity.Quotas.ExternalClients`
> count runs with `IgnoreQueryFilters()` whenever
> `IncludeDeletedObjectsInQuotaEnforcement` is set — which is the default. Each
> create permanently consumes one unit whether or not this script runs. Cleanup
> is org hygiene (no pile of live OAuth clients), not quota relief; quota relief
> for a test org comes from the identity `EnableQuotaEnforcement` exemption list.

Exits 0 always — cleanup failures never fail the test.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# A UUID is the only shape a UiPath external-app Client ID takes. Refusing to
# delete anything that isn't a bare UUID guards against a malformed report.json
# feeding an unexpected value straight into `external-apps delete`.
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)

# Directories that never hold an intent.json worth reading and are huge to walk.
PRUNE_DIRS = {"node_modules", ".git", ".npm-prefix", ".venv", "dist", "build"}

# The build scaffolds into a <routingName> subdirectory, so intent.json sits one
# or two levels down. Bounded so a deep dependency tree cannot stall post_run.
MAX_DEPTH = 6


def _json(path: Path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def intent_client_ids(root: Path):
    """Every `clientId` recorded in an intent.json under the sandbox.

    Exact-name match so the walk does not also pick up `edit-intent.json`, which
    the edit flow writes with a stale id (check_dashboard.py filters it the same
    way for the same reason).
    """
    found = []
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]
        try:
            depth = len(Path(dirpath).resolve().relative_to(root).parts)
        except ValueError:
            # A symlink pointing outside the sandbox — do not follow it further.
            dirnames[:] = []
            continue
        if depth >= MAX_DEPTH:
            dirnames[:] = []
            continue
        if "intent.json" in filenames:
            data = _json(Path(dirpath) / "intent.json")
            if isinstance(data, dict):
                cid = str(data.get("clientId") or "").strip()
                if cid:
                    found.append(cid)
    return found


def report_client_ids() -> list:
    data = _json(Path("report.json"))
    if not isinstance(data, dict):
        return []
    return [
        str(v).strip()
        for v in (data.get("external_app_client_id"), data.get("clientId"))
        if str(v or "").strip()
    ]


def marker_client_ids() -> list:
    try:
        return [Path(".external_app_to_cleanup").read_text(encoding="utf-8").strip()]
    except Exception:
        return []


def main() -> None:
    candidates = intent_client_ids(Path.cwd()) + report_client_ids() + marker_client_ids()

    seen = set()
    for cid in candidates:
        key = cid.lower()
        if key in seen:
            continue
        seen.add(key)
        if not UUID_RE.match(cid):
            print(f"SKIP: client id '{cid}' is not a UUID — refusing to delete", file=sys.stderr)
            continue
        try:
            subprocess.run(
                ["uip", "admin", "external-apps", "delete", cid, "--output", "json"],
                capture_output=True, timeout=60,
            )
            print(f"Deleted external app {cid}", file=sys.stderr)
        except subprocess.TimeoutExpired:
            print(f"TIMEOUT: external-app delete for '{cid}' exceeded 60s; leaving it in place",
                  file=sys.stderr)
        except Exception as e:
            # Any other failure — network, CLI crash, non-zero exit — is non-fatal.
            # Docstring contract: cleanup failures never fail the test.
            print(f"WARN: external-app delete for '{cid}' failed: {e}", file=sys.stderr)

    if not seen:
        print("No external-app client id recorded in this sandbox — nothing to clean up",
              file=sys.stderr)


main()
sys.exit(0)
