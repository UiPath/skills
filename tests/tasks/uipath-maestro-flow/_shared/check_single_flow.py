#!/usr/bin/env python3
"""Assert the Flow project holds one ``.flow`` file, and that the flow is built in it.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_single_flow.py

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
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_check import _HUSK_MAX_NODES, _flow_file_node_count, find_project_dir  # noqa: E402


def single_flow_problem(project_dir: str) -> str | None:
    """Why ``project_dir`` is not one built flow, or ``None`` when it is."""
    flows = sorted(glob.glob(os.path.join(glob.escape(project_dir), "*.flow")))
    counts = [(path, _flow_file_node_count(path)) for path in flows]
    listed = ", ".join(f"{os.path.basename(p)} ({'unreadable' if n is None else f'{n} node(s)'})" for p, n in counts)
    if len(flows) != 1:
        return f"{project_dir} holds {len(flows)} .flow files, expected 1: {listed or 'none'}"
    count = counts[0][1]
    if count is None or count <= _HUSK_MAX_NODES:
        return f"{project_dir} holds only an unbuilt flow: {listed}"
    return None


def main() -> int:
    project_dir = find_project_dir()  # exits with its own message when there is no single Flow project
    problem = single_flow_problem(project_dir)
    if problem:
        print(f"FAIL: {problem}", file=sys.stderr)
        return 1
    print(f"OK: {project_dir} holds one built .flow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
