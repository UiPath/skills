#!/usr/bin/env python3
"""post_run: tear down the faulted-job fixture this task deployed.

Unlike operate/publish_deploy, teardown CANNOT be the agent's job here — the
agent's task is to diagnose, and uninstalling destroys the job records it is
diagnosing. So this backstop owns it, and inherits the known limitation:

A deployment is only uninstallable while its ActivationStatus reads "Active", and
that value decays to "None" within minutes (verified alpha 2026-08-18, uip
1.200.0); after that `deploy uninstall` returns HTTP 400 / errorCode 4007
permanently. The seed deploys, faults a job, then the agent spends several turns
diagnosing — so this often runs past the window and the deployment row survives.

Consequence to accept: this task may leave one history row per run. The package
is always removed. If the row bothers you, Orchestrator UI > Tenant > Solutions.
Fixing this properly needs the decay bug fixed upstream, not a smarter script.

Reads .fault_fixture.json (written by the seed) rather than reconstructing names.
Always exits 0 — post_run must not fail a task over cleanup.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="cleanup_fault_deploy: %(message)s")
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
    env: dict = {}
    if "{" in raw:
        try:
            env = json.loads(raw[raw.index("{"):])
        except json.JSONDecodeError:
            env = {}
    return proc.returncode, env


def main() -> int:
    try:
        fx = json.loads(Path(".fault_fixture.json").read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.info("no readable .fault_fixture.json (%s); nothing to do", exc)
        return 0

    deploy_name = fx.get("deploy_name") or ""
    package_name = fx.get("package_name") or ""
    folder_path = fx.get("folder_path") or ""

    if folder_path:
        code, env = uip("or", "folders", "get", folder_path, timeout=60)
        if not (code == 0 and env.get("Result") == "Success"):
            logger.info("folder %s already gone; deployment de-provisioned", folder_path)
            deploy_name = ""

    if deploy_name:
        code, env = uip("solution", "deploy", "uninstall", deploy_name, "--timeout", "100", "--yes")
        if code == 0 and env.get("Result") == "Success":
            logger.info("uninstalled deployment %s", deploy_name)
        else:
            logger.warning(
                "could not uninstall %s: %s — expected when the activation-decay window has "
                "closed (errorCode 4007). Leaves a cosmetic history row; Orchestrator UI > "
                "Tenant > Solutions removes it.",
                deploy_name, (env.get("Message") or "unknown error")[:200],
            )

    if package_name:
        code, env = uip("solution", "packages", "delete", package_name, "1.0.0", "--yes")
        if code == 0 and env.get("Result") == "Success":
            logger.info("deleted package %s@1.0.0", package_name)
        else:
            message = env.get("Message") or ""
            if "404" in message or "not found" in message.lower():
                logger.info("package %s@1.0.0 not on the tenant; nothing to delete", package_name)
            else:
                logger.warning("could not delete package %s@1.0.0: %s", package_name, message[:200])

    return 0


if __name__ == "__main__":
    sys.exit(main())
