#!/usr/bin/env python3
"""post_run: archive the Automation Hub processes this run created.

`uip ah automations` has no delete verb, so a test process can only be moved out
of the way: it is set to the Business Process flow's Archived status via
`uip ah phases set`. The flow's archive phase/status were resolved by
preflight_ah.py and travel in `seed.json`.

Scope is deliberately narrow: only processes whose NAME carries this run's token
are touched, found through the CLI's own tenant-scoped search — never by id
ranges, never on another tenant. The policy mirrors uipath-maestro-case:

* ``AH_E2E_CLEANUP=always`` (default) — archive regardless of outcome. Use in CI.
* ``AH_E2E_CLEANUP=never`` — leave everything for inspection in the AH UI.

Best-effort: post_run results are informational, so this always exits 0.
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ah_cli import SEED_FILE, describe_failure, items, succeeded, uip_json  # noqa: E402

logging.basicConfig(level=logging.INFO, format="cleanup_ah: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    policy = os.environ.get("AH_E2E_CLEANUP", "always").lower()
    if policy == "never":
        logger.info("AH_E2E_CLEANUP=never; leaving this run's processes in place")
        return 0
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

    for process in ours:
        result = uip_json(["ah", "phases", "set", str(process["Id"]), "--phase", phase, "--status", status])
        if succeeded(result):
            logger.info("archived %s (%s)", process["Id"], process.get("Name"))
        else:
            logger.warning("could not archive %s: %s", process["Id"], describe_failure(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
