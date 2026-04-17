#!/usr/bin/env python3
"""Delete Studio Web solutions uploaded by ``uip flow debug`` during a task.

Wired in via ``post_run`` in flow e2e task YAMLs. Runs from the sandbox CWD
after evaluation completes; finds every ``.uipx`` file under it, reads
``SolutionId``, and best-effort deletes each via ``uip solution delete``.
``.uipx`` files without a ``SolutionId`` are skipped.

Best-effort: failures here never affect pass/fail (post_run results are
informational only), so this script always exits 0.
"""

from __future__ import annotations

import glob
import json
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_solutions: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    paths = glob.glob("**/*.uipx", recursive=True)
    if not paths:
        logger.info("no .uipx files under cwd; nothing to do.")
        return 0

    deleted: list[str] = []
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
        "summary deleted=%d skipped=%d failed=%d",
        len(deleted),
        len(skipped),
        len(failed),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
