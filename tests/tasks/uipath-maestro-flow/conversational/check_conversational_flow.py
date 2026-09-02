#!/usr/bin/env python3
"""Structural checks for a text conversational flow (conversational-agent plugin).

    python3 $TASK_DIR/check_conversational_flow.py settings    # the five-key settings block
    python3 $TASK_DIR/check_conversational_flow.py agent-json  # sidecar agent.json
    python3 $TASK_DIR/check_conversational_flow.py loop        # trigger + success-port loop

Offline — reads the `.flow` source and the inline agent's `agent.json`. No
tenant calls, no agent self-reports. Exit 0 on pass; exit 1 with a `FAIL:` line.
"""

from __future__ import annotations

import glob
import json
import os
import sys

# `_shared/` resolves two ways: locally the task dir sits in the repo so
# `../_shared` works; under coder-eval the task dir is copied in alone
# ($TASK_DIR -> /work/task_dir) and only the repo mount ($SKILLS_REPO_PATH,
# which the other criteria also use) has it.
_TASK_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
_REPO = os.environ.get("SKILLS_REPO_PATH")
_ROOTS = [_TASK_ROOT]
if _REPO:
    _ROOTS.insert(0, os.path.join(_REPO, "tests", "tasks", "uipath-maestro-flow"))
for _root in _ROOTS:
    if os.path.isdir(os.path.join(_root, "_shared")):
        sys.path.insert(0, _root)
        break
else:
    sys.exit(
        "FAIL: cannot locate the _shared helpers. Looked in: "
        + ", ".join(os.path.normpath(r) for r in _ROOTS)
        + ". Set SKILLS_REPO_PATH to the repo root."
    )
from _shared.flow_check import find_project_dir  # noqa: E402

CONV_AGENT = "uipath.agent.conversational"
CORE_AGENT_PREFIX = "uipath.core.agent."
CONV_TRIGGER = "core.trigger.conversation"
WAIT_FOR_MESSAGE = "uipath.conversational.wait-for-message"
MANUAL_TRIGGER = "core.trigger.manual"

# The runtime reads the four derived fields; only the editor derives them from
# `context`, so a CLI-authored flow has to write all five itself.
SETTINGS_KEYS = {
    "context": "",
    "conversationId": "conversationId",
    "exchangeId": "latestExchangeId",
    "messages": "messages",
    "userSettings": "userSettings",
}

# Generated/staging trees the CLI writes beside the sources. Same exclusion set
# the other maestro-flow checkers use.
EXCLUDED_PARTS = {".cli-stage", ".v1stage", ".agent-builder", "_outputs", "v1stage"}


def _fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def _load_flow() -> tuple[str, dict]:
    """Return the (path, parsed) `.flow` that holds the conversational agent node."""
    project_dir = find_project_dir()
    paths = sorted(
        path
        for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
        if not EXCLUDED_PARTS.intersection(path.split(os.sep))
    )
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
        if _conversational_agents(flow):
            print(f"Reading {path}")
            return path, flow

    seen = sorted({str(n.get("type")) for _, f in parsed for n in f.get("nodes") or []})
    sys.exit(
        f"FAIL: no conversational agent node in any .flow under {project_dir} — "
        f"expected {CONV_AGENT} or a {CORE_AGENT_PREFIX}<id> node carrying "
        f"conversationalAgentSettings; node types seen: {seen}"
    )


def _nodes_of(flow: dict, node_type: str) -> list[dict]:
    return [n for n in flow.get("nodes") or [] if n.get("type") == node_type]


def _is_inline(node: dict) -> bool:
    return node.get("type") == CONV_AGENT


def _conversational_agents(flow: dict) -> list[dict]:
    """Chat agent nodes, either flavor.

    Inline is its own node type. An in-solution or published agent reuses
    `uipath.core.agent.<id>` and is marked conversational by its inputs, which
    is what the registry seeds from the release or the sibling agent.json.
    """
    found = []
    for node in flow.get("nodes") or []:
        node_type = str(node.get("type") or "")
        inputs = node.get("inputs") or {}
        if node_type == CONV_AGENT:
            found.append(node)
        elif node_type.startswith(CORE_AGENT_PREFIX) and (
            inputs.get("isConversational") is True
            or "conversationalAgentSettings" in inputs
        ):
            found.append(node)
    return found


def _expression(value: object) -> tuple[str | None, str | None]:
    """Return (expression, error) for one settings binding.

    The contract is a structured `{"type": "jsExpression", "expression": ...}`
    object. A bare `=js:` string is the pre-1.3 form: Studio Web renders it as
    literal text rather than a binding, so it is graded as a failure here.
    """
    if isinstance(value, dict):
        if value.get("type") != "jsExpression":
            return None, (
                f'binding has type {value.get("type")!r}, not "jsExpression" — '
                "only a jsExpression binding is evaluated"
            )
        expression = value.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            return None, "binding object carries no expression text"
        return expression.strip(), None
    if isinstance(value, str):
        return None, (
            f"binding is the bare string {value!r} — a `.flow` binding is a "
            '{"type":"jsExpression","expression":...} object'
        )
    return None, f"binding is {type(value).__name__}, expected a jsExpression object"


def _root_node_id(expression: str) -> str | None:
    """The node id in a `$vars.<id>.output…` expression."""
    parts = expression.lstrip("=").lstrip("$").split(".")
    return parts[1] if len(parts) > 2 and parts[0] == "vars" else None


def check_settings(flow: dict) -> int:
    """All five settings keys bound, and all off the same wait node's context."""
    agents = _conversational_agents(flow)
    if not agents:
        return _fail("no conversational agent node in the flow")

    problems: list[str] = []
    for agent in agents:
        node_id = agent.get("id")
        settings = ((agent.get("inputs") or {}).get("conversationalAgentSettings")) or {}
        if not isinstance(settings, dict):
            problems.append(f"{node_id}: conversationalAgentSettings is not an object")
            continue

        missing = [k for k in SETTINGS_KEYS if k not in settings]
        if missing:
            problems.append(
                f"{node_id}: conversationalAgentSettings is missing {sorted(missing)}. "
                "The runtime reads conversationId, exchangeId, messages and "
                "userSettings; only the editor derives them from context, so a "
                "CLI-authored flow must write all five."
            )
            continue

        roots: set[str] = set()
        for key, suffix in SETTINGS_KEYS.items():
            expression, err = _expression(settings.get(key))
            if err:
                problems.append(f"{node_id}.{key}: {err}")
                continue
            if "conversationContext" not in expression:
                problems.append(
                    f"{node_id}.{key}: {expression!r} does not read a "
                    "wait-for-message `output.conversationContext`"
                )
                continue
            root, _, tail = expression.partition(".conversationContext")
            roots.add(root)
            tail = tail.lstrip(".")
            if suffix and tail != suffix:
                problems.append(
                    f"{node_id}.{key}: reads .{tail or '(nothing)'} but the field "
                    f"is .{suffix}"
                )
            if not suffix and tail:
                problems.append(
                    f"{node_id}.{key}: should bind conversationContext itself, "
                    f"not .{tail}"
                )

        if len(roots) > 1:
            problems.append(
                f"{node_id}: settings read from more than one source {sorted(roots)} "
                "— every key derives from the same wait node's context"
            )
        wait_ids = {n.get("id") for n in _nodes_of(flow, WAIT_FOR_MESSAGE)}
        for root in roots:
            root_id = _root_node_id(root)
            if root_id not in wait_ids:
                problems.append(
                    f"{node_id}: settings are rooted at {root_id!r}, which is not a "
                    f"{WAIT_FOR_MESSAGE} node in this flow — `flow validate` accepts "
                    "invented $vars paths, so this has to be checked here"
                )

    if problems:
        return _fail("; ".join(problems))
    print(f"OK: {len(agents)} conversational agent node(s) carry all five settings keys")
    return 0


def _reaches(start_ids: set[str], targets: set[str], edges: list[dict]) -> bool:
    """True when any `targets` node is reachable from `start_ids` by edges.

    The loop back to the wait node does not have to be direct — a send-message
    between the agent and the wait node is a normal shape.
    """
    seen: set[str] = set()
    queue = [i for i in start_ids if i]
    while queue:
        current = queue.pop()
        if current in targets:
            return True
        if current in seen:
            continue
        seen.add(current)
        queue.extend(
            str(e.get("targetNodeId"))
            for e in edges
            if e.get("sourceNodeId") == current and e.get("targetNodeId")
        )
    return False


def check_loop(flow: dict) -> int:
    """A conversation trigger starts it, and the agent loops back to the wait node.

    The continuation port depends on the flavor: inline agents have no `output`
    and continue on `success`; in-solution and published ones are the reverse.
    """
    problems: list[str] = []

    if not _nodes_of(flow, CONV_TRIGGER):
        problems.append(
            f"no {CONV_TRIGGER} node — without it the packed operate.json carries "
            "no isConversational marker and the flow is not listed as a "
            "Conversational Agent"
        )
    if _nodes_of(flow, MANUAL_TRIGGER):
        problems.append(
            f"{MANUAL_TRIGGER} is still present — flow init scaffolds it and a "
            "chat flow must replace it"
        )
    if not _nodes_of(flow, WAIT_FOR_MESSAGE):
        problems.append(f"no {WAIT_FOR_MESSAGE} node — the chat never takes a turn")

    agents = _conversational_agents(flow)
    if not agents:
        problems.append("no conversational agent node in the flow")

    ports_by_id = {
        n.get("id"): ("success" if _is_inline(n) else "output") for n in agents
    }
    wait_ids = {n.get("id") for n in _nodes_of(flow, WAIT_FOR_MESSAGE)}
    edges = flow.get("edges") or []

    # Only the continuation edge is graded. `escalation`, `context` and `tool`
    # are legitimate wires to somewhere else.
    for agent_id, expected in ports_by_id.items():
        outgoing = [e for e in edges if e.get("sourceNodeId") == agent_id]
        continuation = [e for e in outgoing if e.get("sourcePort") == expected]
        if not continuation:
            flavor = "inline" if expected == "success" else "in-solution/published"
            ports = sorted(
                {str(e.get("sourcePort")) for e in outgoing} or {"(no outgoing edge)"}
            )
            problems.append(
                f"{agent_id} has no edge on {expected!r}, which is how an "
                f"{flavor} conversational agent continues; it leaves on {ports}"
            )
            continue
        # The chat only takes a second turn if the wait node is reachable from
        # there — directly, or through a send-message.
        starts = {str(e.get("targetNodeId")) for e in continuation}
        if not _reaches(starts, wait_ids, edges):
            problems.append(
                f"{agent_id}'s {expected!r} edge leads to {sorted(starts)} and no "
                f"{WAIT_FOR_MESSAGE} node is reachable from there — the chat would "
                "not take another turn"
            )

    if problems:
        return _fail("; ".join(problems))
    print("OK: conversation trigger present and each agent loops back to the wait node")
    return 0


def _solution_root(start_dir: str) -> str:
    """Walk up to the directory holding the `.uipx`, else stay put.

    `find_project_dir()` resolves the *flow* project. An in-solution agent is a
    sibling of it, so the search has to start one level higher.
    """
    current = os.path.abspath(start_dir)
    for _ in range(4):
        if glob.glob(os.path.join(current, "*.uipx")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.abspath(start_dir)


def _agent_json_files(root: str) -> list[str]:
    return [
        path
        for path in glob.glob(os.path.join(root, "**", "agent.json"), recursive=True)
        if not EXCLUDED_PARTS.intersection(path.split(os.sep))
    ]


def _grade_agent_json(path: str, problems: list[str]) -> bool:
    """Append any problems with one agent.json. Returns False if unreadable."""
    try:
        with open(path, encoding="utf-8") as handle:
            agent = json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
        problems.append(f"could not read {path}: {err}")
        return False

    label = os.path.relpath(path)
    settings = agent.get("settings") or {}
    metadata = agent.get("metadata") or {}
    if settings.get("engine") != "conversational-v1":
        problems.append(
            f"{label}: settings.engine is {settings.get('engine')!r}, "
            'expected "conversational-v1"'
        )
    if metadata.get("isConversational") is not True:
        problems.append(
            f"{label}: metadata.isConversational is "
            f"{metadata.get('isConversational')!r}, expected true"
        )
    # The engine reads this, and the conversational node's manifest caps it at 8.
    iterations = settings.get("maxIterations")
    if not isinstance(iterations, int) or iterations > 8:
        problems.append(
            f"{label}: settings.maxIterations is {iterations!r}; the "
            "conversational node caps it at 8"
        )
    system = next(
        (
            m.get("content")
            for m in agent.get("messages") or []
            if m.get("role") == "system"
        ),
        "",
    )
    if not isinstance(system, str) or len(system.strip()) < 20:
        problems.append(
            f"{label}: the system prompt is empty or a stub — the scaffold ships "
            "it blank and it has to be written"
        )
    return True


def check_agent_json(flow_path: str, flow: dict) -> int:
    """The agent behind the chat is a conversational one with a real prompt.

    An inline agent is addressed by `inputs.source`, so it is resolved exactly.
    An in-solution agent's node type carries a solution *resource key*, which is
    not recorded in its agent.json — so the sibling agent projects are graded as
    a set instead, which is unambiguous for a flow that builds one agent.
    """
    agents = _conversational_agents(flow)
    if not agents:
        return _fail("no conversational agent node in the flow")

    root = _solution_root(find_project_dir())
    problems: list[str] = []
    graded: set[str] = set()

    for node in agents:
        if not _is_inline(node):
            continue
        source = (node.get("inputs") or {}).get("source")
        if not isinstance(source, str) or not source:
            problems.append(
                f"inline node {node.get('id')!r} carries no inputs.source — it "
                "must hold the UUID agent init returned"
            )
            continue
        matches = [
            path
            for path in _agent_json_files(root)
            if os.path.basename(os.path.dirname(path)) == source
        ]
        if not matches:
            problems.append(f"no agent.json directory named {source} under {root}")
            continue
        for path in matches:
            if _grade_agent_json(path, problems):
                graded.add(path)

    if any(not _is_inline(n) for n in agents) and not graded:
        # Project-backed agents: grade every conversational agent.json present.
        candidates = _agent_json_files(root)
        conversational = []
        for path in candidates:
            try:
                with open(path, encoding="utf-8") as handle:
                    if (json.load(handle).get("settings") or {}).get(
                        "engine"
                    ) == "conversational-v1":
                        conversational.append(path)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                continue
        if not conversational:
            return _fail(
                f"no conversational agent.json found under {root} — this task "
                "builds the agent, so one must exist on disk (a published agent "
                "would have none, but the sandbox has no tenant)"
            )
        for path in conversational:
            if _grade_agent_json(path, problems):
                graded.add(path)

    if problems:
        return _fail("; ".join(problems))
    print(f"OK: {len(graded)} conversational agent.json file(s) configured")
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in {"settings", "loop", "agent-json"}:
        return _fail("usage: check_conversational_flow.py {settings|loop|agent-json}")
    check = argv[0]
    flow_path, flow = _load_flow()
    if check == "settings":
        return check_settings(flow)
    if check == "loop":
        return check_loop(flow)
    return check_agent_json(flow_path, flow)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
