#!/usr/bin/env python3
"""Deploy-lifecycle artifact + metadata check.

Asserts the artifacts `uip codedagent pack` / `deploy` produce in
`.uipath/`, and that `pyproject.toml` carries the four fields the
deployment guide flags as required (`name`, `version`, `description`,
`authors`). Without `authors`, packaging fails with `Project authors
cannot be empty`.

Checks:
  1. `deploy-smoke/pyproject.toml` has `name`, `version`,
     `description`, and `authors`. No `[build-system]`.
  2. `deploy-smoke/.uipath/` exists and contains a `*.nupkg` file
     (proof that `pack` ran successfully).
  3. `deploy-smoke/invoke-output.txt` exists, is non-empty, and the
     `file_contains` criterion in the YAML separately checks that it
     surfaces an `https://` URL — kept here as a complementary
     "non-empty" guard.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("deploy-smoke")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def check_pyproject() -> None:
    text = _read_text(ROOT / "pyproject.toml")
    if "[build-system]" in text:
        sys.exit("FAIL: pyproject.toml contains a [build-system] section")
    for needle in ("name", "version", "description", "authors"):
        if needle not in text:
            sys.exit(
                f"FAIL: pyproject.toml is missing `{needle}` — "
                "deployment guide requires all four fields."
            )
    print("OK: pyproject.toml has name, version, description, authors")


def check_pack_artifacts() -> None:
    uipath_dir = ROOT / ".uipath"
    if not uipath_dir.is_dir():
        sys.exit(
            f"FAIL: {uipath_dir} does not exist — `uip codedagent pack` "
            "did not run."
        )
    nupkgs = sorted(uipath_dir.glob("*.nupkg"))
    if not nupkgs:
        sys.exit(
            f"FAIL: no .nupkg file in {uipath_dir} — pack did not produce "
            "the expected package artifact."
        )
    print(f"OK: {uipath_dir.name}/{nupkgs[0].name} exists ({len(nupkgs)} package(s) total)")


def check_invoke_output() -> None:
    path = ROOT / "invoke-output.txt"
    text = _read_text(path)
    if not text.strip():
        sys.exit(f"FAIL: {path.name} is empty — `uip codedagent invoke` produced no output")
    if "https://" not in text:
        sys.exit(f"FAIL: {path.name} does not contain a monitoring URL (no `https://` substring)")
    print(f"OK: {path.name} captured {len(text)} bytes of invoke stdout (with monitoring URL)")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_pack_artifacts()
    check_invoke_output()


if __name__ == "__main__":
    main()
