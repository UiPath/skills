#!/usr/bin/env python3
"""Locate emitted ``.bpmn`` files and run ``uip maestro bpmn validate`` on every one.

Usage (from a task's run_command, cwd = sandbox root):

    python3 $REFERENCE_DIR/_shared/validate_bpmn.py [--budget SECONDS]

Plays the role ``uipath-maestro-flow/_shared/validate_flow.py`` plays for the
flow suite. Exit 0 iff at least one file was found and EVERY selected file
validates; otherwise exit 1 after naming the failing file.

Why not ``for f in $(find …); do validate && exit 0; done``: that loop passes
as soon as ANY file validates. ``uip maestro bpmn init`` leaves a valid
scaffold behind, so a sandbox holding a valid scaffold and an invalid real
process read as a pass (CI run 35501830119, devcon_expense_approval). Flow's
helper validates every flow under the project and fails on the first bad one;
this does the same.

Discovery: EVERY ``.bpmn`` under the sandbox (excluding ``node_modules`` and
tool caches). Not only project-registered files: on that same CI run the
agent's real process sat outside the initialised project while the valid
scaffold sat inside it, so a project-scoped rule still read as a pass.
``validate`` is offline, so one attempt per file is enough.

Timeouts are budgeted across the whole run, not per file. A per-file cap is
the wrong unit here precisely because the loop above exists to grade several
files: two slow files each finishing inside their own cap still overrun the
criterion, the harness SIGKILLs the shell, and its buffered stdout — the only
record of which file stalled — is discarded. ``validate_flow.py`` documents
that same failure. So :data:`DEFAULT_BUDGET_SECONDS` is an aggregate wall-clock
deadline: each file gets whatever is left of it, and an overrun is reported
from here, named, and flushed. The default is
:data:`CRITERION_TIMEOUT_SECONDS` -- the timeout every caller sets -- minus
:data:`BUDGET_HEADROOM_SECONDS` for interpreter start, discovery, and
writing the failure message. A caller on a different criterion
timeout passes ``--budget``.

Every print is flushed for the same reason: on an overrun the harness keeps
nothing this process has not already written.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

CRITERION_TIMEOUT_SECONDS = 180
BUDGET_HEADROOM_SECONDS = 10
DEFAULT_BUDGET_SECONDS = CRITERION_TIMEOUT_SECONDS - BUDGET_HEADROOM_SECONDS
SKIP_PARTS = {"node_modules", ".npm-prefix", ".venv"}


def _bpmn_files() -> list[Path]:
    root = Path.cwd()
    candidates = [
        p for p in root.rglob("*.bpmn") if not (SKIP_PARTS & set(p.parts))
    ]
    return sorted(candidates)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate every .bpmn under the sandbox."
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET_SECONDS,
        metavar="SECONDS",
        help=(
            "aggregate wall-clock budget for validating every file "
            f"(default: {DEFAULT_BUDGET_SECONDS}, sized for a "
            f"{CRITERION_TIMEOUT_SECONDS}s criterion timeout)"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    budget = args.budget
    deadline = time.monotonic() + budget

    files = _bpmn_files()
    if not files:
        print("FAIL: no .bpmn file found under the sandbox", file=sys.stderr, flush=True)
        return 1
    rc = 0
    for path in files:
        print(f"Validating {path}", flush=True)
        # Whatever is left of the aggregate budget, so a fast file hands its
        # unused share to a slow one. Never below 1s: a non-positive timeout
        # would raise instead of running.
        per_file = max(1, int(deadline - time.monotonic()))
        try:
            proc = subprocess.run(
                ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
                capture_output=True,
                text=True,
                timeout=per_file,
            )
        except subprocess.TimeoutExpired:
            print(
                f"FAIL: validate timed out after {per_file}s on {path} "
                f"(aggregate budget {budget}s)",
                file=sys.stderr,
                flush=True,
            )
            return 1
        if proc.returncode != 0:
            tail = (proc.stdout or proc.stderr or "").strip()[-1500:]
            print(
                f"FAIL: validate failed for {path}\n{tail}",
                file=sys.stderr,
                flush=True,
            )
            rc = 1
    if rc == 0:
        print(f"OK: {len(files)} .bpmn file(s) validate", flush=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
