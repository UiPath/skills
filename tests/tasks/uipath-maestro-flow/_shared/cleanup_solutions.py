#!/usr/bin/env python3
"""Delete Studio Web solutions uploaded by ``uip flow debug`` during a task.

Wired in via ``post_run`` in flow e2e task YAMLs. Runs from the sandbox CWD
after evaluation completes; finds every ``.uipx`` file under it, reads
``SolutionId``, and best-effort deletes each via ``uip solution delete``.
``.uipx`` files without a ``SolutionId`` are skipped.

Cleanup policy is controlled by the ``FLOW_E2E_CLEANUP`` env var:

* ``always`` (default) — delete regardless of outcome. Use in CI.
* ``never`` — delete nothing. Use when actively debugging locally so the
  solution stays available in Studio Web for inspection.

Best-effort: failures here never affect pass/fail (post_run results are
informational only), so this script always exits 0.
"""

from __future__ import annotations

import glob
import json
import logging
import os
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_solutions: %(message)s")
logger = logging.getLogger(__name__)


def _resolve_policy() -> str:
    policy = os.environ.get("FLOW_E2E_CLEANUP", "always").lower()
    if policy not in ("always", "never"):
        logger.warning(
            "FLOW_E2E_CLEANUP=%r is invalid (expected always|never); treating as 'always'",
            policy,
        )
        return "always"
    return policy


def main() -> int:
    paths = glob.glob("**/*.uipx", recursive=True)
    if not paths:
        logger.info("no .uipx files under cwd; nothing to do.")
        return 0

    policy = _resolve_policy()
    deleted: list[str] = []
    preserved: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for path in paths:
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("could not read %s: %s", path, e)
            skipped.append(path)
            continue

        sid = data.get("SolutionId")
        if not sid:
            logger.info("no SolutionId in %s, skipping", path)
            skipped.append(path)
            continue

        if policy == "never":
            logger.info(
                "FLOW_E2E_CLEANUP=never; preserving %s (delete later with: uip solution delete %s)",
                sid,
                sid,
            )
            preserved.append(sid)
            continue

        r = subprocess.run(
            ["uip", "solution", "delete", sid, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode == 0:
            logger.info("deleted %s (from %s)", sid, path)
            deleted.append(sid)
        else:
            logger.warning(
                "failed to delete %s (exit %d): %s",
                sid,
                r.returncode,
                r.stderr.strip()[:300],
            )
            failed.append(sid)

    logger.info(
        "summary policy=%s deleted=%d preserved=%d skipped=%d failed=%d",
        policy,
        len(deleted),
        len(preserved),
        len(skipped),
        len(failed),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
