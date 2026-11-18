#!/usr/bin/env python3
"""DevToolsFlow: an inline agent that uses the tenant's "GitHubMcp" MCP server.

Kept in the task's own folder because the Studio Web sandbox mounts only this
folder and the skill-level `_shared/` (not `inline_agent/_shared/`).

  wiring   (offline) the flow has a `uipath.agent.autonomous` node and a
           `uipath.agent.resource.mcp.*` node joined agent.tool -> mcp.input,
           and the inline agent project carries the matching resource.json
           (`$resourceType: "mcp"`, name "GitHubMcp"), which is what the
           runtime reads the server from. Any project or file name passes.

  run      debug the flow on a public repository and assert the inline agent
           node completed and the named output `answer` states the
           repository's default branch (octocat/Hello-World: "master").

Usage: check_inline_mcp_server_tool.py wiring|run
"""
import json
import os
import sys
from pathlib import Path

_d = os.path.dirname(os.path.abspath(__file__))
# The skill-level _shared (it holds flow_check.py), not inline_agent/_shared.
while _d != os.path.dirname(_d) and not os.path.isfile(os.path.join(_d, "_shared", "flow_check.py")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    _fail,
    _fail_with_capture,
    assert_named_output_contains,
    completed_node_ids_of_type,
    find_flow_file,
    run_debug,
)

AGENT_TYPE = "uipath.agent.autonomous"
MCP_NODE_PREFIX = "uipath.agent.resource.mcp."
SERVER = "GitHubMcp"
INPUTS = {"repository": "octocat/Hello-World", "question": "What is this repository's default branch?"}
EXPECTED_IN_ANSWER = "master"


def _load(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as e:
        _fail(f"cannot read {path}: {e}")


def check_wiring(flow_path):
    flow = _load(flow_path)
    nodes = flow.get("nodes") or []
    agents = [n for n in nodes if n.get("type") == AGENT_TYPE]
    servers = [n for n in nodes if str(n.get("type", "")).startswith(MCP_NODE_PREFIX)]
    if not agents:
        _fail(f"the flow has no inline agent ({AGENT_TYPE})")
    if not servers:
        _fail(f"the flow has no MCP server resource node ({MCP_NODE_PREFIX}*)")
    server_ids = {n["id"] for n in servers}
    wired = [
        a for a in agents
        if any(
            e.get("sourceNodeId") == a["id"] and e.get("sourcePort") == "tool"
            and e.get("targetNodeId") in server_ids and e.get("targetPort") == "input"
            for e in flow.get("edges") or []
        )
    ]
    if not wired:
        _fail("no edge joins an inline agent's 'tool' handle to an MCP server node's 'input' handle")
    agent = wired[0]
    source = (agent.get("inputs") or {}).get("source")
    agent_dir = Path(flow_path).parent / str(source or "")
    if not source or not agent_dir.is_dir():
        _fail(f"the inline agent's inputs.source {source!r} is not a directory beside the flow")
    for path in sorted((agent_dir / "resources").rglob("resource.json")):
        data = _load(path)
        if data.get("$resourceType") == "mcp" and str(data.get("name", "")).lower() == SERVER.lower():
            if not data.get("isEnabled"):
                _fail(f"{path}: the {SERVER} resource is not enabled")
            print(f"OK: {agent['id']} uses {SERVER} through {sorted(server_ids)}; resource {path}")
            return agent["id"]
    _fail(f"no resources/**/resource.json under {agent_dir} declares the {SERVER} MCP server ($resourceType mcp)")


def check_run(payload, agent_id):
    if agent_id not in completed_node_ids_of_type(payload, AGENT_TYPE):
        _fail_with_capture(f"the inline agent {agent_id} did not complete in the debug run")
    print(f"OK: the inline agent {agent_id} completed")
    assert_named_output_contains(payload, "answer", EXPECTED_IN_ANSWER)
    print(f"OK: answer names the default branch {EXPECTED_IN_ANSWER!r}")


def wiring():
    return check_wiring(find_flow_file())


def run():
    agent_id = wiring()
    print(f"debug inputs: {INPUTS}")
    check_run(run_debug(inputs=INPUTS, timeout=540), agent_id)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("wiring", "run"):
        sys.exit(f"usage: {os.path.basename(__file__)} wiring|run")
    (wiring if sys.argv[1] == "wiring" else run)()


if __name__ == "__main__":
    main()
