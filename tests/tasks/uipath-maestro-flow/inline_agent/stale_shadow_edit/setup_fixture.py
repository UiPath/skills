#!/usr/bin/env python3
"""Seed the stale-shadow fixture for skill-flow-inline-agent-stale-shadow.

Copies `fixture/RefundSol/` into the sandbox root (cwd), producing a
pre-existing solution whose Flow project holds an ALREADY-EMBEDDED inline
agent whose derived sidecar on disk is STALE:

    RefundSol/
    ├── RefundSol.uipx
    ├── RefundTriage/
    │   ├── RefundTriage.flow            # self-contained agent node (source of truth)
    │   ├── project.uiproj
    │   ├── operate.json
    │   └── 9d41c7b2-…/agent.json        # STALE derived copy — older prompts,
    │                                    # weaker model, no guardrail, one output
    └── resources/solution_folder/…

This is the state any out-of-band sidecar write leaves behind: the `.flow`
carries the live definition, the sidecar carries whatever was last flushed. The
`.flow` wins — the canvas overwrites the sidecar on the next save. An agent that
"re-syncs" the node from the stale file silently regresses the agent's model,
limits, guardrail, second output, and one of its two prompt bindings.
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
