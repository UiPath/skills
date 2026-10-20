"""Inline-agent contract checkers for the `inline_agent/` Flow tasks.

These checkers assert the inline agent's sidecar contract: the
`uipath.agent.autonomous` node, its resource nodes and edges in the `.flow`,
and the `<agent-uuid>/resources/<id>/resource.json` shapes the agents
runtime reads. That contract is owned by the uipath-agents skill, so
CODEOWNERS lists the agents team on this folder alongside the Flow team.

Each check script imports from this package by putting `inline_agent/` on
`sys.path`:

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from _shared.inline_wiring import find_autonomous_agent_node  # noqa: E402

Tasks reach them as `python3 $REFERENCE_DIR/inline_agent/_shared/<check>.py`
with `reference.directory: ../..` (the uipath-maestro-flow suite root), which
also exposes the suite's `_shared/validate_flow.py`.
"""
