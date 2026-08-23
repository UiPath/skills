#!/usr/bin/env python3
"""Structural checks for an outbound voice flow (uipath-maestro-flow voice plugin).

Usage (from a task's run_command, cwd = sandbox root):
    python3 $TASK_DIR/check_voice_flow.py call-context
    python3 $TASK_DIR/check_voice_flow.py agent-voice

Offline only — reads the ``.flow`` source and the inline agent's ``agent.json``.
No tenant calls, no agent self-reports.

Checks
------
``call-context``
    The plugin's headline wiring rule. The outbound origin
    (``uipath.conversational.voice.create-outgoing-call``) emits
    ``output.callContext``; it must be bound into BOTH the ``uipath.agent.voice``
    node and the ``uipath.conversational.voice.end-call`` node. Either
    serialization is accepted — the persisted Studio Web binding object
    (``{"type": "jsExpression", "expression": "...", "fieldType": ...}``) or a
    ``=js:`` string — because both express the same wiring. ``fieldType`` is not
    graded: the validator never reads it on a ``jsExpression`` binding.

``agent-voice``
    The voice agent's backing directory carries ``settings.voice`` (the block
    ``uip agent init --inline-in-flow --conversational`` does NOT scaffold) and
    still declares ``metadata.isConversational: true``. The agent directory is a
    UUID, so it is located through the voice node's ``inputs.source``.

Exit 0 on pass; exit 1 with a ``FAIL:`` line naming what is wrong.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"),
)
from flow_check import find_project_dir  # noqa: E402

VOICE_AGENT = "uipath.agent.voice"
CREATE_CALL = "uipath.conversational.voice.create-outgoing-call"
END_CALL = "uipath.conversational.voice.end-call"


def _fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def _load_flow() -> tuple[str, dict]:
    """Return the (path, parsed) ``.flow`` that holds the voice agent node."""
    project_dir = find_project_dir()
    paths = sorted(glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True))
    if not paths:
        sys.exit(f"FAIL: no .flow file found under {project_dir}")

    parsed: list[tuple[str, dict]] = []
    for path in paths:
        try:
            with open(path, encoding="utf-8") as handle:
                parsed.append((path, json.load(handle)))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
            sys.exit(f"FAIL: could not read {path}: {err}")

    for path, flow in parsed:
        if any(n.get("type") == VOICE_AGENT for n in flow.get("nodes") or []):
            print(f"Reading {path}")
            return path, flow

    seen = sorted(
        {n.get("type") for _, f in parsed for n in f.get("nodes") or []}
    )
    sys.exit(
        f"FAIL: no {VOICE_AGENT} node in any .flow under {project_dir}; "
        f"node types seen: {seen}"
    )


def _nodes_of(flow: dict, node_type: str) -> list[dict]:
    return [n for n in flow.get("nodes") or [] if n.get("type") == node_type]


def _binding_expression(value: object) -> str | None:
    """Extract the JS expression from a callContext binding, either shape."""
    if isinstance(value, dict):
        expression = value.get("expression")
        return expression if isinstance(expression, str) else None
    if isinstance(value, str):
        return re.sub(r"^=(?:js:)?", "", value.strip())
    return None


def check_call_context(flow: dict) -> int:
    origins = _nodes_of(flow, CREATE_CALL)
    if len(origins) != 1:
        return _fail(
            f"expected exactly 1 {CREATE_CALL} node (the outbound call origin), "
            f"found {len(origins)}"
        )
    origin_id = origins[0].get("id")
    if not isinstance(origin_id, str) or not origin_id:
        return _fail(f"the {CREATE_CALL} node has no id")

    wanted = re.compile(
        r"\$vars\s*\.\s*" + re.escape(origin_id) + r"\s*\.\s*output\s*\.\s*callContext"
    )

    rules = {
        VOICE_AGENT: "conversational-voice-call-context",
        END_CALL: "conversational-voice-end-call-context",
    }

    errors: list[str] = []
    for node_type in (VOICE_AGENT, END_CALL):
        matches = _nodes_of(flow, node_type)
        if len(matches) != 1:
            errors.append(f"expected exactly 1 {node_type} node, found {len(matches)}")
            continue
        node = matches[0]
        raw = (node.get("inputs") or {}).get("callContext")
        if raw is None:
            errors.append(
                f"{node_type} node {node.get('id')!r} has no inputs.callContext "
                f"binding (rule {rules[node_type]})"
            )
            continue
        expression = _binding_expression(raw)
        if not expression:
            errors.append(
                f"{node_type} node {node.get('id')!r} inputs.callContext carries no "
                f"expression: {json.dumps(raw)[:200]}"
            )
            continue
        if not wanted.search(expression):
            errors.append(
                f"{node_type} node {node.get('id')!r} inputs.callContext does not "
                f"reference $vars.{origin_id}.output.callContext (got {expression!r})"
            )
            continue
        print(f"OK      {node_type} binds $vars.{origin_id}.output.callContext")

    if errors:
        return _fail("; ".join(errors))
    return 0


def check_agent_voice(flow_path: str, flow: dict) -> int:
    agents = _nodes_of(flow, VOICE_AGENT)
    if len(agents) != 1:
        return _fail(f"expected exactly 1 {VOICE_AGENT} node, found {len(agents)}")
    source = (agents[0].get("inputs") or {}).get("source")
    if not isinstance(source, str) or not source:
        return _fail(
            f"{VOICE_AGENT} node {agents[0].get('id')!r} has no inputs.source "
            f"(the inline agent directory's ProjectId)"
        )

    agent_json = os.path.join(os.path.dirname(flow_path), source, "agent.json")
    if not os.path.exists(agent_json):
        found = sorted(
            glob.glob(os.path.join(os.path.dirname(flow_path), "*", "agent.json"))
        )
        return _fail(
            f"inputs.source {source!r} does not resolve to an agent.json "
            f"(looked for {agent_json}); agent.json files present: {found}"
        )
    try:
        with open(agent_json, encoding="utf-8") as handle:
            agent = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
        return _fail(f"could not read {agent_json}: {err}")

    errors: list[str] = []
    voice = (agent.get("settings") or {}).get("voice")
    if not isinstance(voice, dict) or not voice:
        errors.append(
            "settings.voice is missing or empty — `uip agent init "
            "--inline-in-flow --conversational` does not scaffold it, it must be "
            "added by hand"
        )
    elif not str(voice.get("model") or "").strip():
        errors.append("settings.voice.model is empty (the realtime speech model)")
    else:
        print(f"OK      settings.voice.model = {voice['model']!r} in {agent_json}")

    if (agent.get("metadata") or {}).get("isConversational") is not True:
        errors.append(
            "metadata.isConversational is not true — the agent was scaffolded "
            "without --conversational"
        )
    else:
        print("OK      metadata.isConversational is true")

    if errors:
        return _fail("; ".join(errors))
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in {"call-context", "agent-voice"}:
        print(
            "usage: check_voice_flow.py {call-context|agent-voice}",
            file=sys.stderr,
        )
        return 2

    flow_path, flow = _load_flow()
    if argv[0] == "call-context":
        return check_call_context(flow)
    return check_agent_voice(flow_path, flow)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
