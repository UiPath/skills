#!/usr/bin/env python3
"""Stage the agent-visible plugin root: the plugin tree WITHOUT the eval's own fixtures.

``agent.plugins[].path`` is not just a skills pointer — coder_eval bind-mounts it
read-only into every task container at its host path (docker_runner
``_auto_mount``). Pointing it at the repo root therefore hands the agent under
test ``tests/tasks/``: the task YAMLs, the graders, and the ``*.reference.flow``
golden answers. A real run did exactly that (``find / -iname "*.pdf"`` ->
``tests/tasks/uipath-maestro-flow/multi_node/billing_dispute_resolution/``).

So the experiments point at ``$SKILLS_REPO_PATH/.plugin-root`` instead, and every
runner stages it with this script before ``coder-eval run``. Skip the staging and
the plugin loads no skills — loud, never a silent re-open of the hole.

Usage:
    python tests/scripts/stage_plugin_root.py [--dest DIR]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Everything the plugin needs to load, plus the pre_run hook scripts the docker
# experiments invoke from inside the mount. Nothing else: no tests/tasks, no
# tests/fixtures, no tests/experiments.
STAGED_PATHS = (
    ".claude-plugin",
    "skills",
    "commands",
    "hooks",
    "preview",
    "tests/scripts",
    # Both send-telemetry twins read skillsVersion from $CLAUDE_PLUGIN_ROOT.
    "version-manifest.json",
)

DEFAULT_DEST = ".plugin-root"


def stage(repo_root: Path, dest: Path) -> Path:
    dest = dest.resolve()
    if dest == repo_root or dest in repo_root.parents:
        sys.exit(f"stage_plugin_root: refusing to stage over {dest}")
    for rel in STAGED_PATHS:
        if dest == (repo_root / rel) or (repo_root / rel) in dest.parents:
            sys.exit(f"stage_plugin_root: dest must not sit inside a staged source: {dest}")

    if dest.exists():
        shutil.rmtree(dest)

    for rel in STAGED_PATHS:
        src = repo_root / rel
        if not src.exists():
            sys.exit(f"stage_plugin_root: missing source {src}")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            # symlinks=True never dereferences, so a link into tests/tasks cannot
            # be staged as real files; the sweep below then refuses the link itself.
            shutil.copytree(src, target, symlinks=True)
            continue
        shutil.copy2(src, target, follow_symlinks=False)

    for parent, dirs, files in os.walk(dest):
        for name in dirs + files:
            link = Path(parent) / name
            if not link.is_symlink():
                continue
            shutil.rmtree(dest)
            sys.exit(f"stage_plugin_root: symlink in a staged source: {link}")

    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--dest", type=Path, default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    dest = args.dest if args.dest is not None else repo_root / DEFAULT_DEST
    staged = stage(repo_root, dest)
    print(staged)


if __name__ == "__main__":
    main()
