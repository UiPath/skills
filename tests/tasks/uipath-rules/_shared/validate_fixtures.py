#!/usr/bin/env python3
"""`uip rules validate` over every fixture this suite stages. Needs the CLI, not a tenant.

A fixture is the starting point a task hands the agent. One that the CLI refuses fails its task
before the agent's edit is looked at, and nothing else notices: no test stages the fixtures, and
the two that nothing reads are where `graph_extend_brownfield`'s string-encoded
`entry-points.json` sat (MST-18847).

The repair fixtures are expected to be refused -- being refused is the task. They are required
to be refused, so a fixture someone quietly repairs stops silently grading nothing.

Not wired into CI by this change: a job that runs it needs a runner with the CLI, which is an
edit to a shared workflow and belongs with whoever owns it. Run it by hand from the repository
root after touching a fixture, and before relying on one as a starting point:

    python3 tests/tasks/uipath-rules/_shared/validate_fixtures.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixture_inventory import DELIBERATELY_BROKEN, is_sound, projects, rel  # noqa: E402


def validate(project: Path) -> tuple[bool, str]:
    """Whether `uip rules validate` passes, and what it said.

    Run against a copy: `validate` is read-only today, but a fixture is committed state and a
    check that mutates one would rewrite the repo from CI.
    """
    with tempfile.TemporaryDirectory() as work:
        copied = Path(work) / project.name
        shutil.copytree(project, copied)
        completed = subprocess.run(
            ["uip", "rules", "validate", str(copied), "--output", "json"],
            capture_output=True, text=True, timeout=180,
        )
    output = completed.stdout or completed.stderr
    try:
        start = output.index("{")
        diagnostics = (json.loads(output[start:]).get("Data") or {}).get("Diagnostics") or []
        detail = "; ".join(f"{d.get('Code')}: {d.get('Message')}" for d in diagnostics) or output.strip()
    except (ValueError, AttributeError):
        detail = output.strip()[-800:]
    return completed.returncode == 0, detail


def main() -> int:
    found = projects()
    if not found:
        print("FAIL: no fixture found under the suite — checkout layout drift?")
        return 1
    stale = sorted(name for name in DELIBERATELY_BROKEN if not (Path(__file__).resolve().parent.parent / name).is_dir())
    if stale:
        print(f"FAIL: DELIBERATELY_BROKEN names fixtures that are not there: {stale}")
        return 1

    failures = []
    for project in found:
        passes, detail = validate(project)
        name = rel(project)
        if is_sound(project):
            print(f"{'OK  ' if passes else 'FAIL'} {name}" + ("" if passes else f"\n       {detail}"))
            if not passes:
                failures.append(f"{name} is staged as a sound starting point but `uip rules "
                                f"validate` refuses it: {detail}")
        else:
            print(f"{'OK  ' if not passes else 'FAIL'} {name} (expected invalid)"
                  + (f"\n       {detail}" if not passes else ""))
            if passes:
                failures.append(f"{name} is listed as broken on purpose but now validates clean. "
                                f"Either the repair task has nothing to repair, or the entry "
                                f"belongs out of DELIBERATELY_BROKEN.")

    if failures:
        print(f"\nFAIL — {len(failures)} fixture(s):")
        for failure in failures:
            print(f"  - {failure}")
        print("\nRegenerate a stale entry-points.json with `uip rules refresh <PROJECT_DIR>`; it "
              "keeps every published uniqueId. Never hand-edit it.")
        return 1
    print(f"\nOK — all {len(found)} staged fixture(s) are as the suite expects.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
