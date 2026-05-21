#!/usr/bin/env python3
"""Deploy-to-tenant artifact + metadata check.

Asserts the agent left behind a project ready for the tenant feed:
all four pyproject fields required by the deploy guide (`name`,
`version`, `description`, `authors`), no `[build-system]`, and a
`.uipath/*.nupkg` proving `pack` ran. The `--tenant` flag itself is
matched by `command_executed` in the YAML — this script verifies the
artifacts a successful `deploy` produces alongside it.

Also checks that `uipath.json` configures `packOptions` to exclude the
`data/` directory from the package. `packOptions` is the documented
knob for controlling package contents, and is otherwise untested.

Checks:
  1. `tenant-echo/pyproject.toml` has `name`, `version`, `description`,
     and `authors`. No `[build-system]` section.
  2. `tenant-echo/uipath.json` has
     `packOptions.directoriesExcluded` including `data`.
  3. `tenant-echo/.uipath/` contains at least one `*.nupkg` file.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("tenant-echo")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_pyproject() -> None:
    text = _read_text(ROOT / "pyproject.toml")
    if "[build-system]" in text:
        sys.exit(
            "FAIL: pyproject.toml contains a [build-system] section — "
            "Critical Rule C1 forbids it."
        )
    for needle in ("name", "version", "description", "authors"):
        if needle not in text:
            sys.exit(
                f"FAIL: pyproject.toml is missing `{needle}` — deployment "
                "guide requires all four fields. Tenant publish will reject "
                "the package."
            )
    print("OK: pyproject.toml has name, version, description, authors")


def check_pack_options_excludes_data() -> None:
    """packOptions.directoriesExcluded must keep `data/` out of the package."""
    doc = _load_json(ROOT / "uipath.json")
    pack = doc.get("packOptions") or {}
    excluded = pack.get("directoriesExcluded") or []
    if not isinstance(excluded, list):
        sys.exit(
            f"FAIL: uipath.json `packOptions.directoriesExcluded` should be "
            f"a list, got {type(excluded).__name__}"
        )
    if "data" not in excluded:
        sys.exit(
            f"FAIL: uipath.json `packOptions.directoriesExcluded` does not "
            f"include `data`. The agent must exclude the local-only `data/` "
            f"directory from the published package. Got: {excluded!r}"
        )
    print(
        f"OK: uipath.json packOptions.directoriesExcluded = {excluded!r} "
        f"(keeps data/ out of the package)"
    )


def check_pack_artifacts() -> None:
    uipath_dir = ROOT / ".uipath"
    if not uipath_dir.is_dir():
        sys.exit(
            f"FAIL: {uipath_dir} does not exist — `uip codedagent deploy` "
            "did not produce a package directory."
        )
    nupkgs = sorted(uipath_dir.glob("*.nupkg"))
    if not nupkgs:
        sys.exit(
            f"FAIL: no .nupkg in {uipath_dir} — pack stage of deploy did "
            "not produce the expected artifact."
        )
    print(
        f"OK: {uipath_dir.name}/{nupkgs[0].name} exists "
        f"({len(nupkgs)} package(s) total)"
    )


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_pack_options_excludes_data()
    check_pack_artifacts()


if __name__ == "__main__":
    main()
