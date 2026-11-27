#!/usr/bin/env python3
"""Grade a build whose content says "draft" but never asks to see the shape first.

The word names a stage or a task, not draft mode, so the agent builds: the plan
holds at least one built task (a non-empty `data` block), no task keeps a
` [Kind]` outline name, and `uip maestro case validate --strict` reports Valid.

Usage (cwd = sandbox root): check_draft_word_build.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from draft_case import KIND_SUFFIX, fail, is_blank, label_of, load_plan, tasks, validate  # noqa: E402


def problems(doc: dict) -> list[str]:
    found = [task for _, task in tasks(doc)]
    out = []
    outline = [label_of(t) for t in found if KIND_SUFFIX.search(label_of(t))]
    if outline:
        out.append(f"plan keeps outline boxes: {outline}")
    if not any(not is_blank(t) for t in found):
        out.append("plan has no built task: only blank boxes, a draft-mode outline")
    return out


def main() -> int:
    path, doc = load_plan()
    found = problems(doc)
    if found:
        return fail(f"{path}: " + "; ".join(found))
    print(f"Build OK: built task(s) in {path}", flush=True)
    return validate(path)


if __name__ == "__main__":
    sys.exit(main())
