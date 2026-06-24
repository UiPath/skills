#!/usr/bin/env python3
"""Diagnose check: `Project authors cannot be empty` recovery.

Verifies the skill steered the agent to fix the pyproject.toml
rejection rather than wholesale-rewriting the project. The seed has
a working `main.py` and `uipath.json` — those should be preserved.
Only `pyproject.toml` needs to gain a valid `authors` entry.

Checks:
  1. `daily-digest/pyproject.toml`:
     - has `[project]`
     - has a non-empty `authors = [...]` entry
     - retains `name`, `version`, `description`, `dependencies`
     - has NO `[build-system]` section (Critical Rule C1)
  2. `daily-digest/main.py` retains the seeded `@traced()` `main`
     definition (no rewrite).
  3. `daily-digest/.uipath/` exists and contains at least one
     `*.nupkg` — proof that `uip codedagent deploy` got past the
     pyproject rejection and produced a package.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("daily-digest")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def check_pyproject() -> None:
    text = _read_text(ROOT / "pyproject.toml")
    if "[build-system]" in text:
        sys.exit(
            "FAIL: pyproject.toml contains a [build-system] section — "
            "Critical Rule C1 forbids it."
        )
    if "[project]" not in text:
        sys.exit("FAIL: pyproject.toml has no [project] section")

    authors_match = re.search(r"^\s*authors\s*=\s*\[(.*?)\]", text, re.DOTALL | re.MULTILINE)
    if not authors_match:
        sys.exit(
            "FAIL: pyproject.toml has no `authors = [...]` entry — "
            "the original rejection (`Project authors cannot be empty`) "
            "would still apply."
        )
    inner = authors_match.group(1).strip()
    if not inner:
        sys.exit(
            "FAIL: pyproject.toml `authors` list is empty — same "
            "rejection would still apply."
        )
    if "name" not in inner:
        sys.exit(
            f'FAIL: pyproject.toml `authors` entry does not contain a '
            f'`name` field. Expected something like `[{{ name = "..." }}]`. '
            f'Got: {inner!r}'
        )

    for needle in ("name", "version", "description", "dependencies"):
        if needle not in text:
            sys.exit(
                f"FAIL: pyproject.toml lost the `{needle}` field — the "
                "diagnose flow should not strip existing fields."
            )
    print("OK: pyproject.toml has authors[] and all original fields intact")


def check_main_preserved() -> None:
    text = _read_text(ROOT / "main.py")
    for needle in ("class Input", "class Output", "async def main", "@traced"):
        if needle not in text:
            sys.exit(
                f"FAIL: main.py lost the seeded piece `{needle}` — the "
                "diagnose flow should not rewrite the working agent."
            )
    print("OK: main.py retains the seeded Simple Function shape")


def check_pack_artifacts() -> None:
    uipath_dir = ROOT / ".uipath"
    if not uipath_dir.is_dir():
        sys.exit(
            f"FAIL: {uipath_dir} does not exist — `uip codedagent deploy` "
            "either never re-ran after the fix or did not produce a "
            "package directory."
        )
    nupkgs = sorted(uipath_dir.glob("*.nupkg"))
    if not nupkgs:
        sys.exit(
            f"FAIL: no .nupkg in {uipath_dir} — pack stage did not "
            "produce the expected artifact, so the pyproject fix did "
            "not unblock the deploy."
        )
    print(
        f"OK: {uipath_dir.name}/{nupkgs[0].name} exists "
        f"({len(nupkgs)} package(s) total)"
    )


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_main_preserved()
    check_pack_artifacts()


if __name__ == "__main__":
    main()
