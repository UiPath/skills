#!/usr/bin/env python3
"""pre_run: copy the checked-in broken workflow into the sandbox as ./Workflow.json.

Fixtures are static JSON under each task's own fixtures/broken.json rather than
generated in Python, so a reviewer can read exactly what the agent will be handed
and diff it when the DSL changes. Each one is verified to fail in ONE specific way
(see the task's description); a fixture that breaks for a second, accidental
reason makes the grading ambiguous.

The task's own fixtures/ is staged into the same sandbox _setup/ mount point as
this script (sandbox.template_sources), so it resolves as a plain sibling here —
no cross-task argument needed.

Exits non-zero if the fixture is missing — a silent no-op would grade the agent
against an empty sandbox.
"""
import shutil
import sys
from pathlib import Path

src = Path(__file__).resolve().parent / "fixtures" / "broken.json"
if not src.is_file():
    sys.exit(f"seed_fixture.py: fixture not found: {src}")
shutil.copyfile(src, Path("Workflow.json"))
print("OK: seeded ./Workflow.json from fixtures/broken.json")
