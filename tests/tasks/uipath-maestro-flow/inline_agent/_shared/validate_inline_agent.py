#!/usr/bin/env python3
"""Run ``uip agent validate --inline-in-flow`` on every inline agent of a flow.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/inline_agent/_shared/validate_inline_agent.py <Sol>/<Project>/<Project>.flow

This is the agent tool's own contract for an inline agent's directory — "would
Studio Web accept this directory as-is". It checks, in order:

  1. `agent.json` `version` is the agent tool's current schema version
     (`AgentValidationOutdated` otherwise);
  2. the definition itself: `type`, model, engine, mode, the system and user
     messages, the input/output schemas, every `resources/*/resource.json`;
  3. drift: the rows the agent declares in the flow project's
     `bindings_v2.json` match what the agent tool generates from its resources
     (`AgentValidationDrift` otherwise).

Every `uipath.agent.autonomous` node is checked, through its `inputs.source`
directory. Exit 0 iff every one returns `Result: "Success"`.

It replaces the structural `agent.json` check that stood in for it while the
builder SDK's output failed it on two defects: `version: "1.1.0"` and no
agent rows in `bindings_v2.json` (UiPath/builder-sdk#962, fixed by #978 and
#979 in `@uipath/maestro-builder-sdk` 6.16.16). Agent-tool authored output
(`uip agent refresh --inline-in-flow`) passes it too, so it grades the outcome
whichever route wrote the agent.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

AUTONOMOUS_NODE_TYPE = "uipath.agent.autonomous"

# `agent validate` is offline: no tenant call, typically under 5 s. The cap
# turns a hung CLI into a readable failure instead of a harness SIGKILL.
_TIMEOUT_SECONDS = 90


def _fail(message: str) -> int:
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def _agent_dirs(flow_path: Path) -> list[Path] | str:
    """The inline agents' directories, or a failure message."""
    try:
        flow = json.loads(flow_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return f"cannot read {flow_path}: {exc}"
    agents = [n for n in flow.get("nodes") or [] if n.get("type") == AUTONOMOUS_NODE_TYPE]
    if not agents:
        return f"{flow_path} has no {AUTONOMOUS_NODE_TYPE!r} node"
    dirs: list[Path] = []
    for node in agents:
        source = (node.get("inputs") or {}).get("source")
        if not isinstance(source, str) or not source:
            return f"agent node {node.get('id')!r} has no inputs.source"
        agent_dir = flow_path.parent / source
        if not (agent_dir / "agent.json").is_file():
            return f"agent node {node.get('id')!r}: {agent_dir}/agent.json does not exist"
        dirs.append(agent_dir)
    return dirs


def _validate(agent_dir: Path) -> int:
    cmd = ["uip", "agent", "validate", str(agent_dir), "--inline-in-flow", "--output", "json"]
    print(f"Validating {agent_dir}", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=_TIMEOUT_SECONDS)
    except FileNotFoundError:
        return _fail("`uip` is not on PATH")
    except subprocess.TimeoutExpired:
        return _fail(f"`uip agent validate` did not finish within {_TIMEOUT_SECONDS}s for {agent_dir}")
    try:
        envelope = json.loads(result.stdout)
    except json.JSONDecodeError:
        envelope = None
    if not isinstance(envelope, dict):
        return _fail(
            f"`uip agent validate` printed no JSON envelope (exit {result.returncode}) for {agent_dir}\n"
            f"stdout: {result.stdout.strip()}\nstderr: {result.stderr.strip()}"
        )
    if envelope.get("Result") == "Success":
        print(f"OK: {agent_dir.name} — {envelope.get('Code')}")
        return 0
    data = envelope.get("Data") if isinstance(envelope.get("Data"), dict) else {}
    errors = data.get("Errors") or []
    detail = "\n  ".join(str(e) for e in errors) if errors else ""
    return _fail(
        f"{agent_dir.name}: {envelope.get('Code')} — {envelope.get('Message')}"
        + (f"\n  {detail}" if detail else "")
    )


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        return _fail("usage: validate_inline_agent.py <path/to/Name.flow>")
    flow_path = Path(argv[0])
    if not flow_path.is_file():
        return _fail(f"flow file not found: {flow_path}")
    dirs = _agent_dirs(flow_path)
    if isinstance(dirs, str):
        return _fail(dirs)
    rc = 0
    for agent_dir in dirs:
        rc |= _validate(agent_dir)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
