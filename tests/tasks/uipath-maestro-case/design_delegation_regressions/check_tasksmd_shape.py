#!/usr/bin/env python3
"""Advisory: does tasks/tasks.md follow the compact no-build T-entry shape?

Non-gating (`pass_threshold: 0`). Format convention, not case reasoning — the
reasoning invariants are graded by check_case_reasoning_regressions.py, which
reads sdd.md for design so a format lapse cannot hide a design defect.

Observed drift across codex runs from identical input: plain `key: value`
fields, `- key: value` fields, descriptive lanes (`lane: payment confirmation`),
and one plan with no T-entries at all. planning.md § Compact no-build T-entry
shape specifies H2 `## T{N}: task "{Name}"` headings and a numeric `lane`.
"""

import re
import sys
from pathlib import Path

TASKS = Path("tasks/tasks.md")


def main() -> None:
    if not TASKS.is_file():
        print(f"ADVISORY: {TASKS} missing")
        sys.exit(1)
    text = TASKS.read_text(encoding="utf-8", errors="ignore")
    notes: list[str] = []

    t_entries = re.findall(r"(?m)^##\s+T\d+", text)
    if not t_entries:
        notes.append(
            "no `## T{N}:` entries — plan is narrative prose, not the compact "
            "no-build T-entry shape"
        )

    lanes = [m.strip() for m in re.findall(r"(?im)^[-*]?\s*lane:\s*(.+?)\s*$", text)]
    non_numeric = [v for v in lanes if not v.isdigit()]
    if non_numeric:
        notes.append(
            f"{len(non_numeric)}/{len(lanes)} `lane:` values are not numeric "
            f"task-set indices (e.g. {non_numeric[0]!r})"
        )

    if notes:
        print("ADVISORY: compact no-build shape deviations:")
        for n in notes:
            print(f"  - {n}")
        sys.exit(1)

    print(f"OK: compact no-build T-entry shape ({len(t_entries)} entries, numeric lanes)")


if __name__ == "__main__":
    main()
