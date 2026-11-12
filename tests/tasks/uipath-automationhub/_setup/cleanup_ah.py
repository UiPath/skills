#!/usr/bin/env python3
"""post_run: archive the Automation Hub processes this run created.

`uip ah automations` has no delete verb, so a test process can only be moved out
of the way: it is set to the Business Process flow's Archived status via
`uip ah phases set`. The flow's archive phase/status were resolved by
preflight_ah.py and travel in `seed.json`.

Scope is deliberately narrow: only this run's processes are touched — those whose
NAME carries the run token (the CLI's own tenant-scoped search), plus the ids the
call recorder saw this run's successful creates return — never by id ranges, never
on another tenant. Tasks with a fixed prompt and no seed (the
command-shape smoke tasks) pass `--created` instead, which archives exactly the
process ids that this run's successful `automations create` calls returned, read
from the call recorder's log. A fixed name is shared by every concurrent run on
the tenant, so it is never used to pick processes; the flow's archive target is
then read from the tenant. The policy mirrors uipath-maestro-case:

* ``AH_E2E_CLEANUP=always`` (default) — archive regardless of outcome. Use in CI.
* ``AH_E2E_CLEANUP=never`` — leave everything for inspection in the AH UI.

Best-effort: post_run results are informational, so this always exits 0.
"""

from __future__ import annotations

import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ah_cli import (  # noqa: E402
    SEED_FILE,
    archive_target,
    business_process_flow,
    describe_failure,
    items,
    succeeded,
    uip_json,
)

logging.basicConfig(level=logging.INFO, format="cleanup_ah: %(message)s")
logger = logging.getLogger(__name__)

CALL_LOG = os.path.join(".uip-recorder", ".calls.jsonl")


def archive(processes: list[dict], phase: str, status: str) -> None:
    for process in processes:
        try:
            result = uip_json(["ah", "phases", "set", str(process["Id"]), "--phase", phase, "--status", status])
        except (OSError, RuntimeError, KeyError, ValueError) as exc:  # the tenant switch can raise
            logger.warning("could not archive %s: %s", process["Id"], exc)
            continue
        if succeeded(result):
            logger.info("archived %s (%s)", process["Id"], process.get("Name"))
        else:
            logger.warning("could not archive %s: %s", process["Id"], describe_failure(result))


def created_ids(call_log: str = CALL_LOG) -> list[int]:
    """Process ids returned by this run's successful `automations create` calls."""
    if not os.path.exists(call_log):
        return []
    ids: list[int] = []
    with open(call_log, encoding="utf-8") as handle:
        for line in handle:
            call = json.loads(line) if line.strip() else {}
            args = call.get("args") or []
            is_create = any(args[i:i + 2] == ["automations", "create"] for i in range(len(args) - 1))
            if is_create and call.get("result") == "Success" and call.get("data_id") is not None:
                ids.append(int(call["data_id"]))
    return sorted(set(ids))


def archive_created() -> int:
    ids = created_ids()
    if not ids:
        logger.info("no successful create in %s; nothing to clean", CALL_LOG)
        return 0
    flows = uip_json(["ah", "idea-flows", "list"])
    flow = business_process_flow(items(flows)) if succeeded(flows) else None
    target = archive_target(flow) if flow else None
    if not target:
        logger.warning("no Business Process flow with an Archived status; cannot archive %s", ids)
        return 0
    archive([{"Id": process_id} for process_id in ids], *target)
    return 0


def main(argv: list[str]) -> int:
    try:
        return clean(argv)
    except Exception as exc:  # noqa: BLE001 — post_run is best-effort and must exit 0
        logger.warning("cleanup aborted: %s", exc)
        return 0


def clean(argv: list[str]) -> int:
    if os.environ.get("AH_E2E_CLEANUP", "always").lower() == "never":
        logger.info("AH_E2E_CLEANUP=never; leaving this run's processes in place")
        return 0
    if argv == ["--created"]:
        return archive_created()
    return archive_this_run()


def archive_this_run() -> int:
    if not os.path.exists(SEED_FILE):
        logger.info("no %s; nothing to clean", SEED_FILE)
        return 0

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

    # Token search, plus the ids the recorder saw created: a create whose name dropped
    # the token is still this run's process and must not stay live on the shared tenant.
    ours = {process_id: {"Id": process_id} for process_id in created_ids()}
    listing = uip_json(["ah", "automations", "list", "--search", token, "--limit", "50"])
    if succeeded(listing):
        ours.update({p["Id"]: p for p in items(listing) if token in str(p.get("Name", ""))})
    else:
        logger.warning("search failed: %s", describe_failure(listing))
    if not ours:
        logger.info("no processes named with %s and no recorded create; nothing to clean", token)
        return 0

    archive(list(ours.values()), phase, status)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
