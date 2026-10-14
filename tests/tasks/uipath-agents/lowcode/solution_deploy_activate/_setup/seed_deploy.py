#!/usr/bin/env python3
"""pre_run: seed the sandbox with the pre-built EchoSol solution under a
run-unique name, and record that name in ``deploy_seed.json``.

The task promotes a solution the fixture already ships — authoring is out of
scope, so the fixture supplies a validated `EchoAgent` (input `message`, output
`reply`) and every graded step is a `uip solution` promotion step.

Why the run-unique suffix: package name, package version and deployment name are
all tenant-global keys. Two replicates promoting `EchoSol@1.0.0` at once would
collide on publish, fight over one deployment record, and each other's cleanup
would tear down the sibling's deployment mid-run. `uip solution pack` derives the
package name from the solution folder name (`-n` default), so renaming the copied
folder — and its `.uipx` alongside it — is enough to give every run its own
package, deployment and provisioned folder.

`SolutionId` is re-minted for the same reason: the fixture carries a literal one,
and it is a Studio Web identity if the agent uploads en route.

Also ensures the deployment's parent folder (`Shared/uipath-agents`, named in the
prompt) exists, so the task does not depend on tenant pre-state.

Writes ``deploy_seed.json`` (consumed by ``check_deploy_activate.py`` and
``cleanup_deploy.py``):

    {"solution_name": "EchoSol1a2b3c4d", "package_version": "1.0.0",
     "uuid8": "1a2b3c4d"}
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "_fixtures" / "EchoSol"
VERSION = "1.0.0"
# The prompt names this as the deployment target. `deploy run
# --parent-folder-path` requires it to already exist.
PARENT_FOLDER_PATH = "Shared/uipath-agents"


def uip(*args: str) -> dict:
    try:
        proc = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    raw = proc.stdout or ""
    if "{" not in raw:
        return {}
    try:
        return json.loads(raw[raw.index("{"):])
    except json.JSONDecodeError:
        return {}


def ensure_parent_folder(path: str) -> None:
    """Idempotent create of the deployment's parent folder.

    Non-fatal: on a tenant where this cannot be resolved the deploy itself
    surfaces the error, and failing the seed here would report a tenant
    condition as a task-authoring bug. Race-safe under parallel seeds — a lost
    create is confirmed by re-GET.
    """
    if uip("or", "folders", "get", path).get("Result") == "Success":
        return
    parent, _, name = path.rpartition("/")
    if parent and name:
        uip("or", "folders", "create", name, "--parent", parent)
        if uip("or", "folders", "get", path).get("Result") == "Success":
            print(f"seed_deploy.py: created {path}")
            return
    print(f"seed_deploy.py: WARNING could not ensure {path}", file=sys.stderr)


def main() -> int:
    if not FIXTURE.is_dir():
        print(f"seed_deploy.py: fixture missing at {FIXTURE}", file=sys.stderr)
        return 1

    suffix = uuid.uuid4().hex[:8]
    name = f"EchoSol{suffix}"
    dest = Path.cwd() / name

    shutil.copytree(FIXTURE, dest)
    (dest / "EchoSol.uipx").rename(dest / f"{name}.uipx")

    uipx = dest / f"{name}.uipx"
    doc = json.loads(uipx.read_text())
    doc["SolutionId"] = str(uuid.uuid4())
    uipx.write_text(json.dumps(doc, indent=2))

    ensure_parent_folder(PARENT_FOLDER_PATH)

    seed = {"solution_name": name, "package_version": VERSION, "uuid8": suffix}
    Path("deploy_seed.json").write_text(json.dumps(seed, indent=2))
    print(f"seed_deploy.py: seeded {name} (version {VERSION})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
