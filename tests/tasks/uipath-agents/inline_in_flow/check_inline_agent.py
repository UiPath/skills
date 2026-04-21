#!/usr/bin/env python3
"""Inline agent flow-wiring check.

Reads WeatherSol/WeatherFlow/WeatherFlow.flow (existence asserted by
a file_exists criterion in the task YAML) and verifies:

  1. The flow contains a `uipath.agent.autonomous` node.
  2. The node's `model.source` property points to an existing
     directory (the inline agent's UUID-named subdirectory).
"""

import json
import os
import sys
from pathlib import Path

INLINE_AGENT_NODE_TYPE = "uipath.agent.autonomous"
FLOW_PATH = Path(os.getcwd()) / "WeatherSol" / "WeatherFlow" / "WeatherFlow.flow"


def main():
    try:
        flow = json.loads(FLOW_PATH.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {FLOW_PATH} is not valid JSON: {e}")

    nodes = flow.get("nodes") or []
    agent_nodes = [n for n in nodes if n.get("type") == INLINE_AGENT_NODE_TYPE]
    if not agent_nodes:
        sys.exit(
            f"FAIL: {FLOW_PATH.name} has no node of type "
            f"{INLINE_AGENT_NODE_TYPE!r}"
        )

    agent_node = agent_nodes[0]
    source = (agent_node.get("model") or {}).get("source")
    if not source:
        sys.exit(
            f"FAIL: {INLINE_AGENT_NODE_TYPE} node has no model.source"
        )

    agent_dir = FLOW_PATH.parent / source
    if not agent_dir.is_dir():
        sys.exit(
            f"FAIL: model.source {source!r} does not point to an "
            f"existing directory ({agent_dir})"
        )

    print(
        f"OK: {INLINE_AGENT_NODE_TYPE} node's model.source points to "
        f"inline agent directory {source}"
    )


if __name__ == "__main__":
    main()
