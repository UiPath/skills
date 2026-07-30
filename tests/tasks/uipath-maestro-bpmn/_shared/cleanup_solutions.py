#!/usr/bin/env python3
"""Delete Studio Web solutions created by live Maestro BPMN evals.

The script runs from a task sandbox after evaluation. It finds every solution
manifest, including hidden names such as ``..uipx`` produced by
``uip solution init .``, and best-effort deletes each distinct ``SolutionId``.

Set ``BPMN_E2E_CLEANUP=never`` only when intentionally retaining a solution
for local debugging. Cleanup is enabled by default.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="cleanup_solutions: %(message)s")
logger = logging.getLogger(__name__)


def _resolve_policy() -> str:
    policy = os.environ.get("BPMN_E2E_CLEANUP", "always").lower()
    if policy not in ("always", "never"):
        logger.warning(
            "BPMN_E2E_CLEANUP=%r is invalid (expected always|never); treating as 'always'",
            policy,
        )
        return "always"
    return policy


def _solution_ids() -> list[tuple[str, Path]]:
    discovered: list[tuple[str, Path]] = []
    seen: set[str] = set()

    # pathlib intentionally includes dotfiles. Python's glob module would skip
    # ``..uipx``, which is the manifest name emitted by `solution init .`.
    for path in sorted(Path.cwd().rglob("*.uipx")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("could not read %s: %s", path, exc)
            continue

        solution_id = data.get("SolutionId")
        if not solution_id:
            logger.info("no SolutionId in %s, skipping", path)
            continue
        if solution_id in seen:
            continue

        seen.add(solution_id)
        discovered.append((solution_id, path))

    return discovered


def main() -> int:
    solutions = _solution_ids()
    if not solutions:
        logger.info("no solution manifests with SolutionId under cwd; nothing to do")
        return 0

    policy = _resolve_policy()
    deleted: list[str] = []
    preserved: list[str] = []
    not_uploaded: list[str] = []
    failed: list[str] = []

    for solution_id, path in solutions:
        if policy == "never":
            logger.info(
                "BPMN_E2E_CLEANUP=never; preserving %s "
                "(delete later with: uip solution delete %s --yes --output json)",
                solution_id,
                solution_id,
            )
            preserved.append(solution_id)
            continue

        try:
            result = subprocess.run(
                ["uip", "solution", "delete", solution_id, "--yes", "--output", "json"],
                capture_output=True,
                text=True,
                # A newly installed development CLI may perform its daily
                # version/tool sync before the first command. Keep cleanup
                # independent of that one-time startup cost.
                timeout=180,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("failed to delete %s: %s", solution_id, exc)
            failed.append(solution_id)
            continue

        if result.returncode == 0:
            logger.info("deleted %s (from %s)", solution_id, path)
            deleted.append(solution_id)
            continue

        message = ""
        try:
            envelope = json.loads(result.stdout or "{}")
            message = envelope.get("Message", "") or ""
        except json.JSONDecodeError:
            message = (result.stdout or "").strip()

        if "404" in message or "Not Found" in message:
            logger.info(
                "solution %s was not uploaded or was already deleted (from %s)",
                solution_id,
                path,
            )
            not_uploaded.append(solution_id)
        else:
            detail = message or result.stderr.strip()
            logger.warning(
                "failed to delete %s (exit %d): %s",
                solution_id,
                result.returncode,
                detail[:300],
            )
            failed.append(solution_id)

    logger.info(
        "summary policy=%s deleted=%d preserved=%d not_uploaded=%d failed=%d",
        policy,
        len(deleted),
        len(preserved),
        len(not_uploaded),
        len(failed),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
