#!/usr/bin/env python3
"""post_run: archive the Automation Hub processes this run created.

`uip ah automations` has no delete verb, so a test process can only be moved out
of the way: it is set to the Business Process flow's Archived status via
`uip ah phases set`. The flow's archive phase/status were resolved by
preflight_ah.py and travel in `seed.json`.

Scope is deliberately narrow: only processes whose NAME carries this run's token
are touched, found through the CLI's own tenant-scoped search — never by id
ranges, never on another tenant. Tasks with a fixed prompt and no seed (the
command-shape smoke tasks) pass `--name "<exact process name>"` instead, which
archives every not-yet-archived process with exactly that name; the flow's archive
target is then read from the tenant. The policy mirrors uipath-maestro-case:

* ``AH_E2E_CLEANUP=always`` (default) — archive regardless of outcome. Use in CI.
* ``AH_E2E_CLEANUP=never`` — leave everything for inspection in the AH UI.

Best-effort: post_run results are informational, so this always exits 0.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ah_cli import (  # noqa: E402
    SEED_FILE,
    TENANT_HOME_MARKER,
    archive_target,
    business_process_flow,
    describe_failure,
    items,
    succeeded,
    uip_json,
)

logging.basicConfig(level=logging.INFO, format="cleanup_ah: %(message)s")
logger = logging.getLogger(__name__)


def drop_tenant_home() -> None:
    """Remove use_tenant.py's login copy (it holds a token) once the run is done."""
    if not os.path.isfile(TENANT_HOME_MARKER):
        return
    with open(TENANT_HOME_MARKER, encoding="utf-8") as handle:
        home = handle.read().strip()
    if home and os.path.basename(home).startswith("ah-tenant-"):
        shutil.rmtree(home, ignore_errors=True)


def archive(processes: list[dict], phase: str, status: str) -> None:
    for process in processes:
        result = uip_json(["ah", "phases", "set", str(process["Id"]), "--phase", phase, "--status", status])
        if succeeded(result):
            logger.info("archived %s (%s)", process["Id"], process.get("Name"))
        else:
            logger.warning("could not archive %s: %s", process["Id"], describe_failure(result))


def archive_by_name(name: str) -> int:
    flows = uip_json(["ah", "idea-flows", "list"])
    flow = business_process_flow(items(flows)) if succeeded(flows) else None
    target = archive_target(flow) if flow else None
    if not target:
        logger.warning("no Business Process flow with an Archived status; cannot archive %r", name)
        return 0
    listing = uip_json(["ah", "automations", "list", "--search", name, "--limit", "50"])
    if not succeeded(listing):
        logger.warning("search failed: %s", describe_failure(listing))
        return 0
    ours = [p for p in items(listing)
            if str(p.get("Name", "")).strip() == name and str(p.get("PhaseStatus", "")).strip().lower() != "archived"]
    if not ours:
        logger.info("no live process named %r; nothing to clean", name)
        return 0
    archive(ours, *target)
    return 0


def main(argv: list[str]) -> int:
    try:
        if os.environ.get("AH_E2E_CLEANUP", "always").lower() == "never":
            logger.info("AH_E2E_CLEANUP=never; leaving this run's processes in place")
            return 0
        if len(argv) == 2 and argv[0] == "--name":
            return archive_by_name(argv[1])
        return archive_this_run()
    finally:
        drop_tenant_home()


def archive_this_run() -> int:
    if not os.path.exists(SEED_FILE):
        logger.info("no %s; nothing to clean", SEED_FILE)
        return 0

    import json
    with open(SEED_FILE, encoding="utf-8") as handle:
        seed = json.load(handle) or {}
    token = seed.get("run_token")
    phase, status = seed.get("archive_phase"), seed.get("archive_status")
    if not token:
        logger.info("seed carries no run_token; nothing to clean")
        return 0
    if not (phase and status):
        logger.warning("flow has no Archived status recorded; cannot archive %s processes", token)
        return 0

    listing = uip_json(["ah", "automations", "list", "--search", token, "--limit", "50"])
    if not succeeded(listing):
        logger.warning("search failed: %s", describe_failure(listing))
        return 0
    ours = [p for p in items(listing) if token in str(p.get("Name", ""))]
    if not ours:
        logger.info("no processes named with %s; nothing to clean", token)
        return 0

    archive(ours, phase, status)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
