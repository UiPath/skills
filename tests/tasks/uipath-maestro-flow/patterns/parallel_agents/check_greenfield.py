#!/usr/bin/env python3
"""Grades parallel-agents: three independent reviewer agents joined on one merge,
then one synthesis agent that reads every reviewer."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import MERGE, fail, load_graph  # noqa: E402

PANEL = 3


def main() -> None:
    g = load_graph()
    agents = g.agents()

    for join in g.ids(MERGE):
        # Each arm's last agent: it reaches the join without passing another agent.
        # Work before the fan-out (an extraction agent) is not part of the panel.
        reviewers = [
            a for a in agents
            if not g.reaches(join, a) and g.reaches(a, join, blocked=[b for b in agents if b != a])
        ]
        independent = [a for a in reviewers if not any(g.reaches(b, a) for b in reviewers if b != a)]
        if len(independent) < PANEL:
            continue

        synthesis = [s for s in agents if g.reaches(join, s) and all(g.reads(s, r) for r in independent)]
        if not synthesis:
            fail(f"no agent after {join} reads every reviewer ({', '.join(independent)})")

        print(f"PASS: {len(independent)} independent reviewers join on {join}; {synthesis[0]} synthesizes")
        return

    fail(f"no merge joins {PANEL} independent agents: the reviewers do not run in parallel")


if __name__ == "__main__":
    main()
