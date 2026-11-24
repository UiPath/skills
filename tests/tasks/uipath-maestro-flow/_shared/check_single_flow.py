#!/usr/bin/env python3
"""Assert the Flow project holds one ``.flow`` file, and that the flow is built in it
(with ``--allow-unbuilt``: that it is built or is the scaffold's lone manual trigger).

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_single_flow.py [--allow-unbuilt]

``--allow-unbuilt`` keeps the one-file rule but accepts a flow holding only the
``core.trigger.manual`` node that ``uip maestro flow init`` and Studio Web seed,
for a task whose prompt only scaffolds the flow. A flow with no nodes, or whose one
node is anything else (an action, a node with no type), still fails.

A task that asks for one new flow ends with one ``.flow`` in the project:
``<Name>.flow`` from the Node CLI, ``new.flow`` in Studio Web. Studio Web seeds
every Flow project with a trigger-only ``new.flow``; an agent that builds into a
second ``<FlowName>.flow`` beside it leaves the canvas and the entry point on
the empty seed. ``validate_flow.py`` validates both files and passes, so this
check is what fails that outcome.

Only the project folder itself is read: the SDK's working copies live under
``.flow-sdk/``.
"""

from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_check import _HUSK_MAX_NODES, _flow_file_node_count, find_project_dir  # noqa: E402

SCAFFOLD_TRIGGER = "core.trigger.manual"  # the one node `flow init` and Studio Web seed


def _node_types(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return [n.get("type") if isinstance(n, dict) else None for n in json.load(f)["nodes"]]


def single_flow_problem(project_dir: str, allow_unbuilt: bool = False) -> str | None:
    """Why ``project_dir`` is not one built flow (or scaffold, with ``allow_unbuilt``), or ``None``.

    With ``allow_unbuilt`` a flow holding only the scaffold's manual trigger is accepted;
    a flow with no nodes, or one lone node of another type, is not.
    """
    flows = sorted(glob.glob(os.path.join(glob.escape(project_dir), "*.flow")))
    counts = [(path, _flow_file_node_count(path)) for path in flows]
    listed = ", ".join(f"{os.path.basename(p)} ({'unreadable' if n is None else f'{n} node(s)'})" for p, n in counts)
    if len(flows) != 1:
        return f"{project_dir} holds {len(flows)} .flow files, expected 1: {listed or 'none'}"
    count = counts[0][1]
    if count is None or count < 1 or (count <= _HUSK_MAX_NODES and not allow_unbuilt):
        return f"{project_dir} holds only an unbuilt flow: {listed}"
    if count == 1 and _node_types(counts[0][0]) != [SCAFFOLD_TRIGGER]:
        return f"{project_dir} holds one node that is not a {SCAFFOLD_TRIGGER} scaffold: {listed}"
    return None


def main(argv: list[str] | None = None) -> int:
    allow_unbuilt = "--allow-unbuilt" in (sys.argv[1:] if argv is None else argv)
    project_dir = find_project_dir()  # exits with its own message when there is no single Flow project
    problem = single_flow_problem(project_dir, allow_unbuilt)
    if problem:
        print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print(f"OK: {project_dir} holds one {'' if allow_unbuilt else 'built '}.flow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
