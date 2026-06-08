#!/usr/bin/env python3
"""Scaffold a low-code agent, then delete entry-points.json so the review
CLI (`uip agent review`) emits LOWCODE_ENTRY_POINTS_MISSING — a deterministic
rule actually ported in cli PR #2241. Exercises the CLI-first contract
end-to-end: the skill runs the review CLI and surfaces a CLI-emitted rule_id
(which is NOT in the skill catalog but is allowed by Critical Rule 12).
"""

import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.join(
        os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-review", "_shared"
    ),
)
from lowcode_scaffold import write_baseline_lowcode_agent  # noqa: E402

SOLUTION = Path("ReviewSol")


def main() -> None:
    project = write_baseline_lowcode_agent(SOLUTION)
    (project / "entry-points.json").unlink()
    print(
        "Deleted entry-points.json — uip agent review / validate should emit "
        "LOWCODE_ENTRY_POINTS_MISSING"
    )


if __name__ == "__main__":
    main()
