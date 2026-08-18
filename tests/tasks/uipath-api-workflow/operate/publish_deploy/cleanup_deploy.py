#!/usr/bin/env python3
"""post_run: backstop teardown for whatever this run left on the tenant.

NOT the graded path — the task asks the agent to uninstall its own deployment and
check_publish_deploy_job.py grades that it did. This covers the runs that end
without a clean tenant: the agent never reached teardown, its uninstall failed,
the run hit max_turns, or the task timed out. It also deletes the published
package, which the task itself does not ask for.

WHY TEARDOWN IS THE AGENT'S JOB AND NOT THIS SCRIPT'S (verified on alpha
2026-08-18, uip 1.200.0): a deployment can only be uninstalled while its
ActivationStatus reads "Active", and that value decays back to "None" within
minutes of deploying. Once it reads "None", `deploy uninstall` returns HTTP 400 /
errorCode 4007 and the deployment is unremovable via CLI. post_run runs after the
agent has spent minutes starting and polling a job, so it is usually too late.
Reproduced three ways:

  * one-step `deploy run`      -> list showed "None"   -> uninstall 4007
  * one-step `deploy run`      -> list showed "Active" -> decayed to "None"
                                  ~20 min later        -> uninstall 4007
  * `--skip-activate` + `activate`, uninstalled seconds later
                               -> list showed "Active" -> uninstall SUCCEEDED

Mitigating detail: an unremovable row is cosmetic, not a live resource. A failed
uninstall still leaves the provisioned FOLDER de-provisioned in practice, so
nothing keeps running. What lingers is the history row (and, without this script,
the package on the tenant feed).

`deploy list` keeps tombstones — a successfully uninstalled deployment stays
listed. `Operation` + `OperationStatus` are the fields that would identify one,
but `Operation` returns null on this CLI version, so a removed deployment and a
never-removed one look identical. Do not infer teardown success from the list;
trust the uninstall call's own Result.

Best-effort: post_run results are informational, so this always exits 0.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="cleanup_deploy: %(message)s")
logger = logging.getLogger(__name__)


def uip(*args: str, timeout: int = 150) -> tuple[int, dict]:
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


def deployments() -> list[dict]:
    code, env = uip("solution", "deploy", "list", "--limit", "200")
    if code != 0 and not env:
        logger.warning("could not list deployments; skipping deployment cleanup")
        return []
    items = env.get("Data") or []
    if isinstance(items, dict):
        items = items.get("Deployments") or items.get("Items") or items.get("Value") or []
    return [i for i in items if isinstance(i, dict)]


def already_uninstalled(item: dict) -> bool:
    # Correct when the CLI populates Operation; a no-op while it returns null.
    return item.get("Operation") == "Uninstall" and item.get("OperationStatus") == "Successful"


def folder_gone(folder_path: str) -> bool:
    """True when the deploy's provisioned folder no longer exists.

    Stands in for the tombstone check while `Operation` returns null: if the
    folder is gone, the deployment was already de-provisioned, so there is
    nothing for this backstop to do. Without this, a fully successful run — where
    the AGENT did the teardown, as the task asks — still produced a scary
    "could not uninstall (4007)" warning in post_run, because the decay window
    had closed on an already-removed deployment. A warning on every green run is
    a warning nobody reads.
    """
    code, env = uip("or", "folders", "get", folder_path, timeout=60)
    return not (code == 0 and env.get("Result") == "Success")


def main() -> int:
    try:
        uuid8 = (json.loads(Path("seed.json").read_text()).get("uuid8") or "").lower()
    except (OSError, json.JSONDecodeError) as exc:
        logger.info("no readable seed.json (%s); nothing to do", exc)
        return 0
    if not uuid8:
        logger.info("seed.json has no uuid8; nothing to do")
        return 0

    package_name = f"apiwf-pkg-{uuid8}"
    parent = json.loads(Path("seed.json").read_text()).get("parent_folder_path") or "Shared"
    folder_path = f"{parent}/apiwf-deploy-folder-{uuid8}"

    removed = failed = already = 0
    for item in deployments():
        name = str(item.get("Name") or "")
        if uuid8 not in name.lower():
            continue
        if already_uninstalled(item) or folder_gone(folder_path):
            logger.info("deployment %s is already de-provisioned; nothing to undo", name)
            already += 1
            continue
        # --timeout caps the CLI's own uninstall polling (default 360s), which
        # alone would blow coder-eval's post_run cap. If the tenant is slower,
        # the uninstall is still submitted server-side and converges unwatched.
        code, env = uip("solution", "deploy", "uninstall", name, "--timeout", "100", "--yes")
        if code == 0 and env.get("Result") == "Success":
            logger.info("uninstalled deployment %s", name)
            removed += 1
        else:
            failed += 1
            logger.warning(
                "could not uninstall %s: %s — likely the activation-decay window has "
                "closed (errorCode 4007). The folder is de-provisioned either way; the "
                "history row is cosmetic and needs the Orchestrator UI (Tenant > "
                "Solutions) if you want it gone.",
                name, (env.get("Message") or "unknown error")[:200],
            )

    code, env = uip("solution", "packages", "delete", package_name, "1.0.0", "--yes")
    if code == 0 and env.get("Result") == "Success":
        logger.info("deleted package %s@1.0.0", package_name)
        package_deleted = True
    else:
        message = env.get("Message") or ""
        package_deleted = False
        if "404" in message or "not found" in message.lower():
            logger.info("package %s@1.0.0 not on the tenant; nothing to delete", package_name)
        else:
            logger.warning("could not delete package %s@1.0.0: %s", package_name, message[:200])

    logger.info(
        "summary uuid8=%s uninstalled=%d already=%d failed=%d package_deleted=%s",
        uuid8, removed, already, failed, package_deleted,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
