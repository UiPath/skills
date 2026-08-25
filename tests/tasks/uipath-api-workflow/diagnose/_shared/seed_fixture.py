#!/usr/bin/env python3
"""pre_run: copy a checked-in broken workflow into the sandbox as ./Workflow.json.

Usage: seed_fixture.py <task-dir-name>

Fixtures are static JSON under <task-dir>/fixtures/broken.json rather than
generated in Python, so a reviewer can read exactly what the agent will be handed
and diff it when the DSL changes. Each one is verified to fail in ONE specific way
(see the task's description); a fixture that breaks for a second, accidental
reason makes the grading ambiguous.

Exits non-zero if the fixture is missing — a silent no-op would grade the agent
against an empty sandbox.
"""
import shutil
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit("seed_fixture.py: need the task directory name, e.g. `seed_fixture.py export_chain`")

src = Path(__file__).resolve().parent.parent / sys.argv[1] / "fixtures" / "broken.json"
if not src.is_file():
    sys.exit(f"seed_fixture.py: fixture not found: {src}")
shutil.copyfile(src, Path("Workflow.json"))
print(f"OK: seeded ./Workflow.json from {src.parent.parent.name}/fixtures/broken.json")
