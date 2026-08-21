#!/usr/bin/env python3
"""pre_run: copy this task's checked-in broken workflow in as ./Workflow.json.

The fixture is static JSON under fixtures/broken.json rather than generated, so a
reviewer can read exactly what the agent is handed and diff it when the DSL moves.

The fixture has exactly ONE fault: `validate` rejects `activityType: "While"`. It
RUNS correctly on every graded input, `count: 0` included. A second, accidental
fault would make the grading ambiguous, so if you edit the fixture, re-check that
it still runs clean at `count: 0`. That case is load-bearing: when a loop body
never executes, `$context.outputs` is undefined as a whole, so the loop's own
`output.as` must reach it with optional chaining
(`$context?.outputs?.While_1 ?? { results: [] }`) — a bare
`$context.outputs.While_1` throws before any `??` fallback can apply.

Kept per-task rather than in diagnose/_shared/ on purpose: PR #2653 adds a helper
at that shared path, and duplicating it here would collide on merge.

Exits non-zero if the fixture is missing — a silent no-op would grade the agent
against an empty sandbox.
"""
import shutil
import sys
from pathlib import Path

src = Path(__file__).resolve().parent / "fixtures" / "broken.json"
if not src.is_file():
    sys.exit(f"seed_broken.py: fixture not found: {src}")
shutil.copyfile(src, Path("Workflow.json"))
print(f"OK: seeded ./Workflow.json from {src.parent.parent.name}/fixtures/broken.json")
