#!/usr/bin/env python3
"""Validator for all_commands_envelope_e2e.yaml artifacts.

All seven `uip insights jobs` subcommand envelopes must be saved and pass the
shared structural checks (Result, exact Code, Data present). No size-bearing
checks: failure-details grows without bound on busy tenants and is validated
on the same structural terms as the rest.

Also issues one live read of its own (`probe_live_cli`) so an unentitled or
misconfigured tenant fails with the CLI's own message instead of looking like a
run that saved bad files.

Exit 0 on pass, 1 on fail. Reads from the task sandbox cwd (coder_eval
invokes run_command criteria with cwd set to the sandbox root).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_shared = (Path(os.environ["SKILLS_REPO_PATH"]) / "tests" / "tasks" / "uipath-insights" / "_shared"
           if os.environ.get("SKILLS_REPO_PATH")
           else Path(__file__).resolve().parent.parent / "_shared")
sys.path.insert(0, str(_shared))
from envelope_check import CODES, check_envelope, load_envelope, probe_live_cli


def main() -> int:
    errors = 0

    # First, so a tenant that cannot answer Insights queries names itself before
    # the per-file diagnostics, which would otherwise read as bad artifacts.
    if not probe_live_cli():
        errors += 1

    for fname, code in CODES.items():
        data = load_envelope(fname)
        if data is None or not check_envelope(fname, data, code):
            errors += 1

    if errors:
        return 1
    print("OK: all 7 envelopes valid (empty Data passes structurally)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
