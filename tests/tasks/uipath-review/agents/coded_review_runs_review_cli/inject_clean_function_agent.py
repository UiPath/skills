#!/usr/bin/env python3
"""Scaffold a clean coded FUNCTION agent (no injected violation). The test
asserts the skill delegates deterministic checks to the review CLI
(`uip codedagent review`), stays read-only, reads the judgment catalog, and
produces a report — the CLI-first contract for coded agents. No specific
finding is asserted because deterministic detection lives in the CLI.
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
from coded_scaffold import write_baseline_function_agent  # noqa: E402


def main() -> None:
    write_baseline_function_agent(Path("CodedAgent"))
    print("Scaffolded clean coded FUNCTION agent at CodedAgent/")


if __name__ == "__main__":
    main()
