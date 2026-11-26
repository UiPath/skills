#!/usr/bin/env python3
"""Tenant canary for the uipath-rules tenant tasks: is the rules engine there and right?

Each tenant task runs this in `pre_run`. It runs `uip rules debug` on a fixed, known-good
project and checks one output. A failing `pre_run` ends the run as ERROR, so a tenant
outage or an engine regression is not scored as a skill failure.

The project lives in `canary/CanaryRules/` with its manifest named `project.uiproj.canary`,
so nothing in the sandbox looks like a Business Rules project: the agent and the graders
find every `project.uiproj`. The canary builds the project in a temporary folder outside
the sandbox and deletes the Studio Web solution its debug run uploaded.

The case is a row the table reaches only after it passes the first rows, so a wrong
hit policy or a skipped row fails it: creditScore 650 with income 49999 is High.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "canary" / "CanaryRules"
INPUTS = {"creditScore": 650, "income": 49999}
OUTPUT, EXPECTED = "riskBand", "High"
# `pre_run` allows each command 300 seconds, and the cleanup needs some of them.
DEBUG_TIMEOUT = 200

sys.path.insert(0, str(HERE))
import solution_cleanup  # noqa: E402


def fail(message: str) -> int:
    print(f"CANARY FAIL: {message}. The tenant cannot run Business Rules, so this run is not a skill result.")
    return 1


def outputs_of(stdout: str) -> dict:
    """The decisions' outputs by output name. A table answers with a context of its columns."""
    result = (json.loads(stdout).get("Data") or {}).get("result") or {}
    found: dict = {}
    for decision in result.get("decisions") or []:
        value = decision.get("outputs")
        found.update(value if isinstance(value, dict) else {decision.get("decisionName"): value})
    return found


def check(scratch: Path) -> int:
    project = scratch / SOURCE.name
    shutil.copytree(SOURCE, project)
    (project / "project.uiproj.canary").rename(project / "project.uiproj")
    command = ["uip", "rules", "debug", str(project), "--inputs", json.dumps(INPUTS), "--output", "json"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=DEBUG_TIMEOUT)
    except subprocess.TimeoutExpired:
        return fail(f"`uip rules debug` did not answer in {DEBUG_TIMEOUT}s")
    if completed.returncode != 0:
        return fail(f"`uip rules debug` exited {completed.returncode}: {(completed.stdout or completed.stderr)[-1500:]}")
    try:
        actual = outputs_of(completed.stdout).get(OUTPUT)
    except ValueError:
        return fail(f"`uip rules debug` printed no JSON: {completed.stdout[-1500:]}")
    if actual != EXPECTED:
        return fail(f"the engine returned {OUTPUT}={actual!r} for {INPUTS}, expected {EXPECTED!r}")
    print(f"OK: the engine returned {OUTPUT}={actual!r} for {INPUTS}")
    return 0


def main() -> int:
    sandbox = Path.cwd()
    scratch = Path(tempfile.mkdtemp(prefix="rules-canary-"))
    # `solution_cleanup` works on the current folder. The folder is new and empty, so every
    # solution manifest in it after the run is the canary's own.
    os.chdir(scratch)
    try:
        solution_cleanup.record()
        return check(scratch)
    finally:
        try:
            solution_cleanup.delete()
        except Exception as error:  # noqa: BLE001 - a failed cleanup must not hide the result
            print(f"warn: canary cleanup failed, a solution may remain on the tenant: {error}")
        os.chdir(sandbox)
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
