#!/usr/bin/env python3
"""Assert Build it replaced every outline box.

A skeleton validates as well as a built case, so `validate` alone cannot tell
that Build it did anything. Fails when the plan keeps a blank task (an empty
`data` block), keeps a ` [Kind]` outline suffix on any task name, or has no task.

Usage (cwd = sandbox root): check_no_blank_boxes.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_case import KIND_SUFFIX, fail, is_blank, label_of, load_plan, tasks  # noqa: E402


def main() -> int:
    path, doc = load_plan()
    found = [task for _, task in tasks(doc)]
    blank = [label_of(t) for t in found if is_blank(t)]
    if blank:
        return fail(f"{path} still has blank boxes: {blank}")
    suffixed = [label_of(t) for t in found if KIND_SUFFIX.search(label_of(t))]
    if suffixed:
        return fail(f"{path} keeps the [Kind] outline suffix on: {suffixed}")
    if not found:
        return fail(f"{path} has no task")
    print(f"OK: {path} has {len(found)} built task(s), no outline box")
    return 0


if __name__ == "__main__":
    sys.exit(main())
