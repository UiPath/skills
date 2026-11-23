#!/usr/bin/env python3
"""Assert the graded BPMN file declares each given element id.

Mirrors Flow's `_shared/flow_contains.py` id check. A BPMN simulation targets a
component by its `.bpmn` element id, and on cli `main` `simulation add` rejects
an id that is not a real element (`locateComponent`), so a simulation-CRUD task
must author its targets before simulating them. This verifies they exist.

Usage: check_bpmn_contains.py --bpmn-name <Name> <id> [<id> ...]
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET


def _tasks_root(start: str) -> str:
    path = start
    while True:
        if os.path.isdir(os.path.join(path, "_shared")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return start
        path = parent


sys.path.insert(0, _tasks_root(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_check import parse_bpmn  # noqa: E402


def _element_ids(root: ET.Element) -> set[str]:
    ids: set[str] = set()
    for element in root.iter():
        value = element.attrib.get("id")
        if value:
            ids.add(value)
    return ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bpmn-name", required=True)
    parser.add_argument("ids", nargs="+")
    args = parser.parse_args()

    path, root = parse_bpmn(args.bpmn_name)
    present = _element_ids(root)
    missing = [component_id for component_id in args.ids if component_id not in present]
    if missing:
        sys.exit(
            f"FAIL: {path} is missing element id(s): "
            f"{', '.join(missing)}. Present ids: {sorted(present)}"
        )
    print(f"OK: {path} declares {', '.join(args.ids)}")


if __name__ == "__main__":
    main()
