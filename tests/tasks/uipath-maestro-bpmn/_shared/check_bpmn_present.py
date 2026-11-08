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

`--contains TEXT` (repeatable) also asserts each literal TEXT is in that file. It
replaces `file_contains` criteria pinned to the root `<Name>.bpmn`, which fail the
builder-SDK skill's `<Name>/<Name>.bpmn` on layout alone.

Usage: check_bpmn_present.py <Name> [--contains TEXT ...]   (basename without `.bpmn`)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import fail, find_bpmn_file  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Assert the graded BPMN file exists.")
    parser.add_argument("name", help="basename without `.bpmn`")
    parser.add_argument(
        "--contains",
        action="append",
        default=[],
        metavar="TEXT",
        help="literal text the file must contain (repeatable)",
    )
    args = parser.parse_args(argv)
    name = args.name.removesuffix(".bpmn")
    path = find_bpmn_file(name)
    if args.contains:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        missing = [needle for needle in args.contains if needle not in text]
        if missing:
            fail(f"{path} does not contain {missing}")
    print(f"OK: {name}.bpmn present at {path}" + (f", contains {args.contains}" if args.contains else ""))


if __name__ == "__main__":
    main()
