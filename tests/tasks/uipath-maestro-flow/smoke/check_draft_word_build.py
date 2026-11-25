#!/usr/bin/env python3
"""Grade a build whose content says "draft" but never asks to see the shape first.

The word names a step (draft a reply), not draft mode, so the agent builds: the
Flow holds at least one real action node (not only `core.logic.mock` boxes) and
`uip maestro flow validate` reports Valid. With `--no-outline-mocks`, a leftover
`core.logic.mock` box with a `[Kind]` outline label also fails.

Usage (cwd = sandbox root): check_draft_word_build.py [--no-outline-mocks]
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _shared.draft_flow import KIND_SUFFIX, MOCK, action_nodes, fail, label_of, load_flow, validate  # noqa: E402


def main(argv: list[str] = ()) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-outline-mocks", action="store_true")
    args = ap.parse_args(list(argv))
    path, doc = load_flow()
    if args.no_outline_mocks:
        outline = [n.get("id") for n in action_nodes(doc) if n.get("type") == MOCK and KIND_SUFFIX.search(label_of(n))]
        if outline:
            return fail(f"{path} keeps mock outline boxes: {outline}")
    real = [n for n in action_nodes(doc) if n.get("type") != MOCK]
    if not real:
        return fail(f"{path} has no real action node: only mock boxes, a draft-mode outline")
    print(f"Build OK: {len(real)} real action node(s) in {path}", flush=True)
    return validate(path)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
