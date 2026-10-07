#!/usr/bin/env python3
"""Assert the graded BPMN file exists — wherever the arm's workflow put it.

Replaces `file_exists` criteria that pinned `<Name>.bpmn` to the workspace root. That
shape is v1's: the raw-XML skill writes one file where it stands. The builder-SDK
skill scaffolds with `uip maestro bpmn init`, which emits `<Name>/<Name>.bpmn` (or
`<Name>Solution/<Name>/<Name>.bpmn` outside a solution) and tells the agent to keep
exactly one emitted copy THERE — so an agent following its skill to the letter failed
the criterion on layout alone (skill-bpmn-debug-not-validation, run 2026-09-25). Every
`check_*.py` beside these criteria already locates the file with `find_bpmn_file`;
this makes the presence check use the same rule, including its "never grade a stray
draft copy" tie-break.

Usage: check_bpmn_present.py <Name>   (basename without `.bpmn`)
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import find_bpmn_file  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: check_bpmn_present.py <Name>", file=sys.stderr)
        raise SystemExit(2)
    name = sys.argv[1].removesuffix(".bpmn")
    path = find_bpmn_file(name)
    print(f"OK: {name}.bpmn present at {path}")


if __name__ == "__main__":
    main()
