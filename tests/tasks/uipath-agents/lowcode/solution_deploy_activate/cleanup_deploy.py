#!/usr/bin/env python3
"""post_run: tear down whatever this run left on the tenant.

Backstop, not the graded path — the agent is asked to uninstall its own
deployment and `check_deploy_activate.py` grades that it did. This runs after
evaluation and covers every way the run can end without a clean tenant: the
agent never reached the uninstall step, its uninstall failed, the run hit
`max_turns`, or the task timed out.

Removes, in order:

1. The deployment (`deploy uninstall`) — de-provisions the solution folder and
   the resources inside it. Skipped for rows already tombstoned
   (`Operation: Uninstall`, `OperationStatus: Successful`).
2. The published package version (`packages delete`) — otherwise the version
   lingers on the tenant feed.

Scoped by the run-unique solution name in `deploy_seed.json`: a deployment is
ours if its `PackageName` matches, or if its name carries this run's `uuid8`
(the agent chooses the deployment name, so name-matching catches deployments a
partial run created under a different package). Parallel replicates therefore
never tear down each other's work.

Cleanup policy is controlled by the ``AGENT_E2E_CLEANUP`` env var:

* ``always`` (default) — delete regardless of outcome. Use in CI.
* ``never`` — delete nothing. Use when actively debugging locally so the
  deployment stays inspectable in Orchestrator.

Best-effort: post_run results are informational only, so this always exits 0.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="cleanup_deploy: %(message)s")
logger = logging.getLogger(__name__)

# Wall-clock budget for the uninstall loop, leaving headroom inside coder-eval's
# 300s post_run cap for the package delete that follows.
UNINSTALL_BUDGET_S = 200


def uip(*args: str, timeout: int = 120) -> tuple[int, dict]:
    try:
        proc = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("uip %s failed to run: %s", " ".join(args), exc)
        return 1, {}
    raw = proc.stdout or ""
    envelope: dict = {}
    if "{" in raw:
        try:
            envelope = json.loads(raw[raw.index("{"):])
        except json.JSONDecodeError:
            envelope = {}
    return proc.returncode, envelope


def resolve_policy() -> str:
    policy = os.environ.get("AGENT_E2E_CLEANUP", "always").lower()
    if policy not in ("always", "never"):
        logger.warning(
            "AGENT_E2E_CLEANUP=%r is invalid (expected always|never); treating as 'always'",
            policy,
        )
        return "always"
    return policy


def load_seed() -> dict | None:
    seed_path = Path("deploy_seed.json")
    if not seed_path.is_file():
        logger.info("no deploy_seed.json under cwd; nothing to do.")
        return None
    try:
        return json.loads(seed_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("could not read deploy_seed.json: %s", exc)
        return None


def deployments() -> list[dict]:
    code, envelope = uip("solution", "deploy", "list", "--limit", "200")
    if code != 0 and not envelope:
        logger.warning("could not list deployments; skipping deployment cleanup")
        return []
    items = envelope.get("Data") or []
    if isinstance(items, dict):
        items = items.get("Deployments") or items.get("Items") or items.get("Value") or []
    return [i for i in items if isinstance(i, dict)]


def is_ours(item: dict, name: str, uuid8: str) -> bool:
    if item.get("PackageName") == name:
        return True
    return bool(uuid8) and uuid8 in (item.get("Name") or "").lower()


def uninstalled(item: dict) -> bool:
    return item.get("Operation") == "Uninstall" and item.get("OperationStatus") == "Successful"


def main() -> int:
    seed = load_seed()
    if seed is None:
        return 0

    name = seed.get("solution_name") or ""
    version = seed.get("package_version") or ""
    uuid8 = (seed.get("uuid8") or "").lower()
    if not name:
        logger.warning("deploy_seed.json has no solution_name; nothing to do.")
        return 0

    policy = resolve_policy()
    if policy == "never":
        logger.info(
            "AGENT_E2E_CLEANUP=never; preserving %s (tear down later with: "
            "uip solution deploy uninstall <name> --yes && "
            "uip solution packages delete %s %s --yes)",
            name, name, version,
        )
        return 0

    # coder-eval caps a post_run step at 300s and kills it on overrun, which
    # would skip the package delete below. Stop starting new uninstalls once the
    # budget is spent; a run only ever creates one deployment, so this bites only
    # when a partial run left several behind.
    deadline = time.monotonic() + UNINSTALL_BUDGET_S

    removed, already, failed, abandoned = 0, 0, 0, 0
    for item in deployments():
        if not is_ours(item, name, uuid8):
            continue
        deployment_name = item.get("Name") or ""
        if uninstalled(item):
            already += 1
            continue
        if not deployment_name:
            continue
        if time.monotonic() >= deadline:
            abandoned += 1
            logger.warning(
                "post_run budget spent; leaving %s for manual teardown "
                "(uip solution deploy uninstall %s --yes)",
                deployment_name, deployment_name,
            )
            continue
        # `--timeout` caps the CLI's uninstall polling (default 360s), which alone
        # would blow the 300s coder-eval allows a post_run step. Poll for 100s;
        # if the tenant is slower than that the uninstall is still submitted
        # server-side and converges without us watching.
        code, envelope = uip(
            "solution", "deploy", "uninstall", deployment_name,
            "--timeout", "100", "--yes", timeout=150,
        )
        if code == 0:
            logger.info("uninstalled deployment %s", deployment_name)
            removed += 1
        else:
            failed += 1
            logger.warning(
                "failed to uninstall %s: %s",
                deployment_name,
                (envelope.get("Message") or "unknown error")[:300],
            )

    package_deleted = False
    if version:
        code, envelope = uip("solution", "packages", "delete", name, version, "--yes")
        if code == 0:
            package_deleted = True
            logger.info("deleted package %s@%s", name, version)
        else:
            message = envelope.get("Message") or ""
            # Never published (or already gone) — nothing to clean up.
            if "404" in message or "Not Found" in message or "not found" in message.lower():
                logger.info("package %s@%s not on the tenant; nothing to delete", name, version)
            else:
                logger.warning(
                    "failed to delete package %s@%s: %s", name, version, message[:300]
                )

    logger.info(
        "summary solution=%s uninstalled=%d already_uninstalled=%d failed=%d "
        "abandoned=%d package_deleted=%s",
        name, removed, already, failed, abandoned, package_deleted,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
