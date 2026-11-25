#!/usr/bin/env python3
"""Deletes only the Studio Web solutions a `uip rules debug` run created.

`rules debug` uploads a solution per run, so an e2e task has to clean up after itself or they
accumulate on the tenant. An id is deleted only when neither its manifest's path nor the id
itself was on disk when `record` ran before the agent -- so a manifest that was already there,
copied to a new path, is not a new solution.

The record is the whole of the evidence, deliberately. Scoping by a directory name was tried and
was worse than useless: `uip rules init <NAME>` writes the manifest to
`<NAME>Solution/<NAME>Solution.uipx`, beside the project rather than inside it, so a filter on
the project name matched nothing and the cleanup deleted nothing at all. A path an agent writes
is not proof of anything; the before-and-after record is.

Ownership is inferred from that record, not proven: only `uip rules debug` knows which solution
it made, and `post_run` never sees its output. Where ownership is unknown the id is left on the
tenant, and no record at all deletes nothing -- a leftover solution is tidied by hand, a deleted
one is not. Narrowing this to a trusted create record is MST-18847.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STATE = Path(".rules-e2e-solutions.json")


def manifests() -> list[Path]:
    """Every `.uipx` in the sandbox, wherever the agent or the CLI put it."""
    return sorted(Path().rglob("*.uipx"))


def solution_id(path: Path) -> str | None:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("SolutionId") or None
    except (OSError, ValueError):
        return None


def record() -> None:
    """What is on disk before the agent runs: these are not ours to delete."""
    found = {str(path): solution_id(path) for path in manifests()}
    STATE.write_text(json.dumps(found), encoding="utf-8")
    print(f"recorded {len(found)} pre-existing manifest(s): {sorted(found)}")


def delete() -> None:
    # No record is no evidence. Treating a missing state file as "nothing was here before" is
    # exactly the glob this replaces, so a `pre_run` that was dropped or failed would silently
    # restore the behaviour rather than show itself.
    if not STATE.exists():
        print(f"no {STATE} written by `solution_cleanup.py record`; deleting nothing")
        return
    before = json.loads(STATE.read_text(encoding="utf-8"))
    known_ids = {value for value in before.values() if value}
    deleted, failed, skipped = [], [], []
    for path in manifests():
        found = solution_id(path)
        if not found:
            continue
        if str(path) in before or found in known_ids:
            skipped.append(f"{path} ({found})")
            continue
        completed = subprocess.run(["uip", "solution", "delete", found, "--yes", "--output", "json"],
                                   timeout=120)
        (deleted if completed.returncode == 0 else failed).append(found)
    print(f"deleted {deleted or 'nothing'}")
    if failed:
        print(f"FAILED to delete, still on the tenant: {failed}")
    if skipped:
        print(f"left alone, on disk before the run: {skipped}")


if __name__ == "__main__":
    # A project name used to scope the search and no longer does; it is still accepted so a task
    # that passes one is not an error, and ignored.
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode in ("record", "delete"):
        {"record": record, "delete": delete}[mode]()
    else:
        sys.exit("usage: solution_cleanup.py record|delete")
