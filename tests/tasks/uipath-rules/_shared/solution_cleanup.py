#!/usr/bin/env python3
"""Deletes only the Studio Web solutions a `uip rules debug` run created.

`rules debug` uploads a solution per run, so an e2e task has to clean up after
itself or the solutions accumulate on the tenant. Deleting by a glob over every
`.uipx` in the workspace is how that was first written, and it deletes whatever
a manifest names — including a solution that was already there, which no run of
this task created and which deleting destroys.

`record` runs before the agent and writes down what is already on disk.
`delete` runs after it and deletes an id only when all three hold:

  * its manifest sits under the project directory the task names, not anywhere
    in the tree;
  * that path was not on disk before the run;
  * that **id** was not on disk before the run — so copying a manifest that was
    already there to a new path does not turn it back into a delete target.

What this cannot do is prove the tenant solution came from this run. Only
`uip rules debug` knows that, and `post_run` never sees its output;
`uip solution list` would confirm it against the tenant but registers on
preview builds only (UiPath/cli solution-tool/src/tool.ts), so a task running a
stable CLI cannot call it. An id this skips is left on the tenant, which is the
safe way round: a leftover solution is tidied by hand, a deleted one is not.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STATE = Path(".rules-e2e-solutions.json")


def manifests(project: str) -> list[Path]:
    """Every `.uipx` under the named project directory, wherever the agent put it."""
    return sorted(path for path in Path().rglob("*.uipx") if project in path.parts)


def solution_id(path: Path) -> str | None:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("SolutionId") or None
    except (OSError, ValueError):
        return None


def record(project: str) -> None:
    """What is on disk before the agent runs: these are not ours to delete."""
    found = {str(path): solution_id(path) for path in manifests(project)}
    STATE.write_text(json.dumps(found), encoding="utf-8")
    print(f"recorded {len(found)} pre-existing manifest(s) under {project}/: {sorted(found)}")


def delete(project: str) -> None:
    # No record is no evidence. Treating a missing state file as "nothing was here before" is
    # exactly the glob this replaces, so a `pre_run` that was dropped or failed would silently
    # restore the behaviour rather than show itself.
    if not STATE.exists():
        print(f"no {STATE} written by `solution_cleanup.py record`; deleting nothing")
        return
    before = json.loads(STATE.read_text(encoding="utf-8"))
    known_ids = {value for value in before.values() if value}
    deleted, skipped = [], []
    for path in manifests(project):
        found = solution_id(path)
        if not found:
            continue
        if str(path) in before or found in known_ids:
            skipped.append(f"{path} ({found})")
            continue
        subprocess.run(["uip", "solution", "delete", found, "--yes", "--output", "json"], timeout=120)
        deleted.append(found)
    print(f"deleted {deleted or 'nothing'}")
    if skipped:
        print(f"left alone, on disk before the run: {skipped}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    name = sys.argv[2] if len(sys.argv) > 2 else ""
    if mode in ("record", "delete") and name:
        {"record": record, "delete": delete}[mode](name)
    else:
        sys.exit("usage: solution_cleanup.py record|delete <PROJECT_DIR_NAME>")
