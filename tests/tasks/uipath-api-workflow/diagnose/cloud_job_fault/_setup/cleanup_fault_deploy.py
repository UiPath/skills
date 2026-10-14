#!/usr/bin/env python3
"""post_run: tear down the faulted-job fixture this task deployed.

Unlike operate/publish_deploy, teardown cannot be the agent's job here — the
agent's task is to diagnose, and uninstalling destroys the job records it is
diagnosing (`uip or jobs get` then returns Result: Failure with an empty State).

`solution deploy list` keeps uninstalled deployments as history rows; `Operation`
= `Uninstall` with `OperationStatus` = `Successful` identifies one. A 4007
"cannot be uninstalled" on a retry means the deployment is already gone, not that
it is stuck.

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

    if deploy_name:
        code, env = uip("solution", "deploy", "uninstall", deploy_name, "--timeout", "100", "--yes")
        if code == 0 and env.get("Result") == "Success":
            logger.info("uninstalled deployment %s", deploy_name)
        else:
            logger.warning(
                "could not uninstall %s: %s — a 4007 here means it was already removed.",
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
