#!/usr/bin/env python3
"""Inline agent layout check.

Finds the UUID-named subdirectory under the WeatherSol solution
(i.e. an inline-in-flow agent) and verifies the expected files and
subdirectories are present. Presence only — does not inspect JSON
field contents.

Required in <uuid>/:
  - agent.json
  - flow-layout.json
  - evals/eval-sets/
  - features/
  - resources/

Forbidden in <uuid>/ (inline agents do not have these):
  - entry-points.json
  - project.uiproj
"""

import os
import re
import sys
from pathlib import Path

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

REQUIRED_FILES = ("agent.json", "flow-layout.json")
REQUIRED_DIRS = ("evals/eval-sets", "features", "resources")
FORBIDDEN_FILES = ("entry-points.json", "project.uiproj")


def main():
    solution_root = Path(os.getcwd()) / "WeatherSol"
    if not solution_root.is_dir():
        sys.exit(f"FAIL: Solution directory not found: {solution_root}")

    uuid_dirs = [
        p for p in solution_root.rglob("*")
        if p.is_dir() and UUID_RE.match(p.name)
    ]
    if len(uuid_dirs) == 0:
        sys.exit(
            f"FAIL: No UUID-named subdirectory found anywhere under "
            f"{solution_root} — an inline-in-flow agent must create one."
        )
    if len(uuid_dirs) > 1:
        sys.exit(
            f"FAIL: Expected exactly one UUID-named subdirectory, found "
            f"{len(uuid_dirs)}: "
            f"{[str(d.relative_to(solution_root)) for d in uuid_dirs]}"
        )

    agent_dir = uuid_dirs[0]
    print(f"OK: Inline agent subdirectory: {agent_dir.relative_to(solution_root)}")

    for name in REQUIRED_FILES:
        if not (agent_dir / name).is_file():
            sys.exit(f"FAIL: Missing required file {agent_dir / name}")
    print(f"OK: required files present ({', '.join(REQUIRED_FILES)})")

    for name in REQUIRED_DIRS:
        if not (agent_dir / name).is_dir():
            sys.exit(f"FAIL: Missing required directory {agent_dir / name}")
    print(f"OK: required directories present ({', '.join(REQUIRED_DIRS)})")

    for name in FORBIDDEN_FILES:
        if (agent_dir / name).exists():
            sys.exit(
                f"FAIL: inline agent must NOT contain {name}, "
                f"but {agent_dir / name} exists"
            )
    print(f"OK: forbidden files absent ({', '.join(FORBIDDEN_FILES)})")


if __name__ == "__main__":
    main()
