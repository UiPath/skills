#!/usr/bin/env python3
"""Enforce the EVFX- fixture contract (tests/tasks/uipath-test/fixtures/README.md).

Two invariants, both of which the 2026-08-05 nightly violated:

1. **Sole ownership** — an EVFX- fixture name may be referenced by exactly one
   task file. Two tasks touching one mutable fixture is how execution_rerun
   destroyed the history flaky_tests_analysis reads.
2. **Namespace discipline** — a task may only reference EVFX- names whose
   namespace segment matches its own, so a task cannot quietly reach into a
   sibling's fixtures.

Exit 1 on violation. Runs from any directory:

    python3 tests/tasks/uipath-test/fixtures/check-collisions.py
"""
import re
import sys
from pathlib import Path

# The task directory is this script's parent — resolved from __file__ so the
# check runs from any working directory, not just the repo root.
TASK_DIR = Path(__file__).resolve().parent.parent
EVFX = re.compile(r"EVFX-[A-Z]+(?:-[A-Za-z0-9]+)*")

# Namespace segment -> the single task file allowed to own it.
OWNERS = {
    "RERUN": "execution_rerun_failed_integration.yaml",
    "FLAKY": "flaky_tests_analysis.yaml",
    "SIGNOFF": "release_signoff_wait_report_e2e.yaml",
    "ORG": "organize_testcases_into_testsets.yaml",
    "READY": "integration_release_readiness_qa_lead.yaml",
    "JUNIT": "test_report_junit_export.yaml",
    "SCAFFOLD": "project_scaffold_build.yaml",
    "CURATE": "testset_curation_by_label_build.yaml",
    "SCHEMA": "customfield_schema_multiscope_build.yaml",
}


def main() -> int:
    if not TASK_DIR.is_dir():
        print(f"error: {TASK_DIR} not found", file=sys.stderr)
        return 2

    refs: dict[str, set[str]] = {}
    errors: list[str] = []

    # rglob, not glob: tasks may sit in nested leaf directories, and a
    # non-recursive scan would report the contract as valid while silently
    # ignoring a collision introduced by a nested task.
    for path in sorted(TASK_DIR.rglob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        for name in set(EVFX.findall(text)):
            refs.setdefault(name, set()).add(path.name)

            ns = name.split("-")[1]
            owner = OWNERS.get(ns)
            if owner is None:
                errors.append(
                    f"{path.name}: references {name}, but namespace "
                    f"EVFX-{ns}-* has no declared owner. Add it to OWNERS "
                    f"and to tests/tasks/uipath-test/fixtures/README.md."
                )
            elif owner != path.name:
                errors.append(
                    f"{path.name}: references {name}, which belongs to "
                    f"{owner}. A task may only use its own namespace."
                )

    for name, files in sorted(refs.items()):
        if len(files) > 1:
            errors.append(
                f"{name} is referenced by {len(files)} tasks "
                f"({', '.join(sorted(files))}). An EVFX- fixture must have "
                f"exactly one owner."
            )

    if errors:
        print("EVFX fixture contract violations:\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(
            "\nSee tests/tasks/uipath-test/fixtures/README.md for the contract.",
            file=sys.stderr,
        )
        return 1

    print(f"EVFX fixture contract OK — {len(refs)} fixture names, no collisions.")
    for name, files in sorted(refs.items()):
        print(f"  {name:24s} {next(iter(files))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
