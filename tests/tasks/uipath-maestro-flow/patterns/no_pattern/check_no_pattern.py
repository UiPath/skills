#!/usr/bin/env python3
"""Grades the negative gate: a linear reshape with no decisions carries no agent,
review, routing, fan-out or chat scaffolding."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import DECISION, END, MERGE, SWITCH, fail, load_graph  # noqa: E402

SCAFFOLDING = ("uipath.agent.", "uipath.core.agent.", "uipath.human-in-the-loop", "uipath.conversational.", DECISION, SWITCH, MERGE)


def main() -> None:
    g = load_graph()

    retrofitted = sorted(f"{n} ({g.type_of(n)})" for n in g.ids(*SCAFFOLDING))
    if retrofitted:
        fail(f"pattern scaffolding on a linear process: {', '.join(retrofitted)}")

    ends = g.ids(END)
    if len(ends) != 1:
        fail(f"{len(ends)} End nodes on a process with one outcome")

    print(f"PASS: {len(g.nodes)} nodes, linear, one End")


if __name__ == "__main__":
    main()
