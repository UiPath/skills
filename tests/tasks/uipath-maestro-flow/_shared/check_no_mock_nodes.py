#!/usr/bin/env python3
"""Assert Build it replaced every outline box.

A skeleton validates as well as a built flow, so `validate` alone cannot tell
that Build it did anything. Fails when the Flow keeps a `core.logic.mock` node,
keeps a ` [Kind]` outline suffix on any action label, or has no action node.

Usage (cwd = sandbox root): check_no_mock_nodes.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_flow import KIND_SUFFIX, MOCK, action_nodes, fail, label_of, load_flow  # noqa: E402


def main() -> int:
    path, doc = load_flow()
    actions = action_nodes(doc)
    mocks = [n.get("id") for n in actions if n.get("type") == MOCK]
    if mocks:
        return fail(f"{path} still has mock boxes: {mocks}")
    suffixed = [n.get("id") for n in actions if KIND_SUFFIX.search(label_of(n))]
    if suffixed:
        return fail(f"{path} keeps the [Kind] outline suffix on: {suffixed}")
    if not actions:
        return fail(f"{path} has no action node")
    print(f"OK: {path} has {len(actions)} built action node(s), no outline box")
    return 0


if __name__ == "__main__":
    sys.exit(main())
