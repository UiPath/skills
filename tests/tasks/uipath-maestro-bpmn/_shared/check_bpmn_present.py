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

Usage: check_bpmn_present.py <Name> [--beside FILE]... [--contains TEXT]...
  <Name>      basename without `.bpmn`; Studio Web's `<Name>/Process.bpmn` counts as the same file
  --beside    a file that must sit next to the BPMN (`project.uiproj`, `operate.json`)
  --contains  text the BPMN must contain
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import fail, find_bpmn_file  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(prog="check_bpmn_present.py")
    parser.add_argument("name")
    parser.add_argument("--beside", action="append", default=[])
    parser.add_argument("--contains", action="append", default=[])
    args = parser.parse_args()
    name = args.name.removesuffix(".bpmn")
    path = Path(find_bpmn_file(name))
    missing = [f for f in args.beside if not (path.parent / f).is_file()]
    if missing:
        fail(f"{', '.join(missing)} missing beside {path}")
    text = path.read_text(encoding="utf-8") if args.contains else ""
    absent = [t for t in args.contains if t not in text]
    if absent:
        fail(f"{path} does not contain {absent}")
    print(f"OK: {name}.bpmn present at {path}")


if __name__ == "__main__":
    main()
