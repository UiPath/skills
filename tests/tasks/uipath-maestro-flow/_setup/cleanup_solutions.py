#!/usr/bin/env python3
"""Delete Studio Web solutions uploaded by ``uip maestro flow debug`` during a task.

Wired in via ``post_run`` in flow e2e task YAMLs. Runs from the sandbox CWD
after evaluation completes; finds every ``.uipx`` file under it, reads
``SolutionId``, and best-effort deletes each via ``uip solution delete``.
``.uipx`` files without a ``SolutionId`` are skipped. Ids that the INTERIM
Overwrite rotation in ``flow_check.py`` moved away from are read from the
``.rotated-solution-ids`` sidecar beside each ``.uipx`` and deleted too.

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

ROTATED_SOLUTION_IDS_SIDECAR = ".rotated-solution-ids"  # written by flow_check.py


def _solution_ids(uipx_path: str) -> list[tuple[str, str]]:
    """``(solution_id, source)`` pairs for one ``.uipx``: its current id plus any
    ids the Overwrite rotation left on the tenant (sidecar, one per line)."""
    ids: list[tuple[str, str]] = []
    with open(uipx_path) as f:
        data = json.load(f)
    sid = data.get("SolutionId")
    if sid:
        ids.append((sid, uipx_path))
    else:
        logger.info("no SolutionId in %s", uipx_path)
    sidecar = os.path.join(os.path.dirname(uipx_path), ROTATED_SOLUTION_IDS_SIDECAR)
    if os.path.isfile(sidecar):
        with open(sidecar) as f:
            for line in f:
                rotated = line.strip()
                if rotated and all(rotated != known for known, _ in ids):
                    ids.append((rotated, sidecar))
    return ids


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
    not_uploaded: list[str] = []
    failed: list[str] = []

    targets: list[tuple[str, str]] = []
    for uipx_path in paths:
        try:
            ids = _solution_ids(uipx_path)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("could not read %s: %s", uipx_path, e)
            skipped.append(uipx_path)
            continue
        if not ids:
            skipped.append(uipx_path)
        targets.extend(ids)

    for sid, path in targets:
        if policy == "never":
            logger.info(
                "FLOW_E2E_CLEANUP=never; preserving %s (delete later with: uip solution delete %s)",
                sid,
                sid,
            )
            preserved.append(sid)
            continue

        r = subprocess.run(
            ["uip", "solution", "delete", sid, "--yes", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode == 0:
            logger.info("deleted %s (from %s)", sid, path)
            deleted.append(sid)
            continue

        # `uip solution delete` writes its envelope to stdout (including
        # failures); stderr is empty. Parse the envelope to surface the real
        # reason and to distinguish "never uploaded" from genuine failures.
        envelope_msg = ""
        try:
            envelope = json.loads(r.stdout or "{}")
            envelope_msg = envelope.get("Message", "") or ""
        except json.JSONDecodeError:
            envelope_msg = (r.stdout or "").strip()

        if "404" in envelope_msg or "Not Found" in envelope_msg:
            # Solution never registered in Studio Web — `.uipx` carries a
            # locally-generated SolutionId from `solution init`, and tasks
            # that don't `upload`/`flow debug` leave it unregistered.
            # Nothing to clean up server-side.
            logger.info("solution %s not uploaded (from %s); nothing to clean up", sid, path)
            not_uploaded.append(sid)
        else:
            logger.warning(
                "failed to delete %s (exit %d): %s",
                sid,
                r.returncode,
                (envelope_msg or r.stderr.strip())[:300],
            )
            failed.append(sid)

    logger.info(
        "summary policy=%s deleted=%d preserved=%d skipped=%d not_uploaded=%d failed=%d",
        policy,
        len(deleted),
        len(preserved),
        len(skipped),
        len(not_uploaded),
        len(failed),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
