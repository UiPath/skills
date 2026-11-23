#!/usr/bin/env python3
"""Grades batch-ai: a per-item agent inside a loop whose failure moves on to the
next item, and a synthesis agent after the loop that reads the loop's results."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from _shared.flow_graph import CONTINUE_PORT, LOOP, fail, load_graph  # noqa: E402

ERROR_PORT = "error"


def isolated(g, agent: str, loop: str) -> bool:
    errors = g.edges_from(agent, ERROR_PORT)
    return bool(errors) and all(
        (e["targetNodeId"] == loop and e.get("targetPort") == CONTINUE_PORT)
        or g.continues(e["targetNodeId"], loop)
        for e in errors
    )


def main() -> None:
    g = load_graph()

    per_item = [(a, l) for l in g.ids(LOOP) for a in g.agents() if g.inside(a, l)]
    if not per_item:
        fail("no agent inside a loop body: the agent does not run per item")

    # One bad item must not end the batch: the agent's error path stays in the
    # body and closes the iteration, never an End or a Terminate.
    found = [(a, l) for a, l in per_item if isolated(g, a, l)]
    if not found:
        fail("the per-item agent's failure is unwired, leaves the loop, or ends the run: one failure stops the batch")
    agent, loop = found[0]

    # The loop's own results, or a variable a body step accumulates them into,
    # read by the agent or by a step that reshapes them for it.
    sources = [loop, *(n for n in g.nodes if g.inside(n, loop) and g.writes(n))]
    synthesis = [
        a for a in g.agents()
        if not g.inside(a, loop) and g.reaches(loop, a) and any(g.feeds(a, src) for src in sources)
    ]
    if not synthesis:
        fail(f"no agent after loop {loop} reads its results to synthesize the batch")

    print(f"PASS: {agent} runs per item in {loop} with its failure isolated; {synthesis[0]} synthesizes")


if __name__ == "__main__":
    main()
