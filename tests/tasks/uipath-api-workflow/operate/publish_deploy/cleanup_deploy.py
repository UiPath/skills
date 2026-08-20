#!/usr/bin/env python3
"""post_run: backstop teardown for whatever this run left on the tenant.

NOT the graded path — the task asks the agent to uninstall its own deployment and
check_publish_deploy_job.py grades that it did. This covers the runs that end
without a clean tenant: the agent never reached teardown, its uninstall failed,
the run hit max_turns, or the task timed out. It also deletes the published
package, which the task itself does not ask for.

Reading the deploy list correctly matters here. `solution deploy list` keeps
uninstalled deployments as history rows, and the fields that identify one are
`Operation` (`Uninstall`) plus `OperationStatus` (`Successful`). Do NOT use
`ActivationStatus` for this: it reads `None` both before activation and after a
successful uninstall, so it cannot tell the two apart.

Re-attempting an uninstall on an already-uninstalled deployment returns HTTP 400 /
errorCode 4007 ("cannot be uninstalled"). That error means ALREADY GONE, not
"stuck" — hence the `already_uninstalled` guard before every call, which keeps the
log honest and avoids a scary warning on a clean run.

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
    """True when this row is the tombstone of a completed uninstall."""
    return item.get("Operation") == "Uninstall" and item.get("OperationStatus") == "Successful"


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

    removed = failed = already = 0
    for item in deployments():
        name = str(item.get("Name") or "")
        if uuid8 not in name.lower():
            continue
        if already_uninstalled(item):
            logger.info("deployment %s already uninstalled; nothing to undo", name)
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
                "could not uninstall %s: %s — if this is errorCode 4007 the deployment "
                "was already removed (check Operation on its deploy-list row).",
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
