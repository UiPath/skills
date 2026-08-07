#!/usr/bin/env python3
"""Seed the brownfield fixture for skill-flow-inline-agent-legacy-shell.

Copies `fixture/BillingSol/` into the sandbox root (cwd), producing a
pre-existing solution whose Flow project holds a LEGACY-SHELL inline agent:

    BillingSol/
    ├── BillingSol.uipx
    ├── DisputeAnalyst/
    │   ├── DisputeAnalyst.flow          # agent node = shell (no embedded prompts)
    │   ├── project.uiproj
    │   ├── operate.json
    │   └── e5715a3f-…/agent.json        # the stored (derived) sidecar definition
    └── resources/solution_folder/…

The shell + sidecar pair is what a pre-#2636 canvas — or any flag-off canvas
save — leaves on disk: the `uipath.agent.autonomous` node carries only
structural `inputs` (`source` + the two variables arrays) and the definition
(prompts, settings, guardrails, schemas) lives in the UUID sidecar.

`uip maestro flow validate` PASSES on this fixture as-is: the CLI hydrates the
shell from the sidecar. Validation is therefore a regression guard for this
task, not the migration gate — the checker is.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent / "fixture"


def main() -> int:
    if not FIXTURE.is_dir():
        print(f"FAIL: fixture directory not found at {FIXTURE}", file=sys.stderr)
        return 1
    dest = Path.cwd()
    for child in sorted(FIXTURE.iterdir()):
        target = dest / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)
        print(f"seeded {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
