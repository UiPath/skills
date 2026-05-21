#!/usr/bin/env python3
"""Deploy-to-folder + patch-bump-on-redeploy check.

The agent must deploy twice to the same Orchestrator folder. The
second deploy fails with `Version already exists` unless the agent
bumps the patch version in `pyproject.toml` between the deploys
(documented in the skill's Troubleshooting table).

Asserts:
  1. `acme-echo/pyproject.toml` is valid TOML with a `[project]` table.
  2. The `version` follows semver `MAJOR.MINOR.PATCH`.
  3. The `version` is strictly greater than `0.0.1` (the scaffold default
     `uip codedagent new` writes). Any of `0.0.2`, `0.1.0`, `1.0.0`, etc.
     proves a bump happened.
  4. The edit landed: `main.py` mentions the `acme: ` prefix the user
     asked for (otherwise the second deploy would be a no-op rebump).
  5. No `[build-system]` section (Critical Rule C1).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


ROOT = Path(os.getcwd()) / "acme-echo"
PYPROJECT = ROOT / "pyproject.toml"
MAIN = ROOT / "main.py"

SCAFFOLD_VERSION = (0, 0, 1)


def parse_version(text: str) -> tuple[int, int, int]:
    """Return (major, minor, patch) for the version inside [project]."""
    in_project = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_project = stripped == "[project]"
            continue
        if not in_project:
            continue
        m = re.match(r'^\s*version\s*=\s*"([^"]+)"\s*$', line)
        if m:
            parts = m.group(1).split(".")
            if len(parts) != 3:
                fail(f"version {m.group(1)!r} is not semver MAJOR.MINOR.PATCH")
            try:
                return (int(parts[0]), int(parts[1]), int(parts[2]))
            except ValueError:
                fail(f"version {m.group(1)!r} has non-integer components")
    fail("`version =` not found inside [project] in pyproject.toml")
    raise SystemExit(1)  # for type checkers


def main() -> None:
    if not PYPROJECT.is_file():
        fail(f"missing {PYPROJECT}")
    text = PYPROJECT.read_text(encoding="utf-8")

    if re.search(r"^\s*\[build-system\]", text, re.M):
        fail(
            "pyproject.toml has a [build-system] section — Critical Rule C1: "
            "UiPath coded agents do not use a build backend."
        )
    print("OK: pyproject.toml has no [build-system] section")

    version = parse_version(text)
    print(f"OK: pyproject.toml [project].version parses as {version}")
    if version <= SCAFFOLD_VERSION:
        fail(
            f"version {version} is not greater than the scaffold default 0.0.1. "
            "The second deploy fails with `Version already exists` unless the "
            "patch was bumped — bump the version in pyproject.toml between the "
            "two deploys."
        )
    print(
        f"OK: version {version} is greater than the scaffold default 0.0.1 — re-deploy bump happened"
    )

    if not MAIN.is_file():
        fail(f"missing {MAIN}")
    main_text = MAIN.read_text(encoding="utf-8")
    if "acme: " not in main_text:
        fail(
            "main.py does not contain the `acme: ` prefix the user asked for in "
            "the second iteration — the edit was not applied before the second deploy"
        )
    print("OK: main.py contains the `acme: ` prefix (edit applied)")

    print("OK: deploy-to-folder + patch-bump roundtrip verified")


if __name__ == "__main__":
    main()
