#!/usr/bin/env python3
"""Structural checks for a voice flow (uipath-maestro-flow voice plugin).

    python3 $TASK_DIR/check_voice_flow.py call-context          # outbound wiring
    python3 $TASK_DIR/check_voice_flow.py inbound-call-context  # inbound wiring
    python3 $TASK_DIR/check_voice_flow.py agent-voice           # sidecar agent.json
    python3 $TASK_DIR/check_voice_flow.py prompt-inputs [--min-inputs N]

`--min-inputs N` asserts the prompt reads N distinct inputs — use it whenever
the task's prompt supplies more than one value.

Offline — reads the `.flow` source and the inline agent's `agent.json`. No
tenant calls, no agent self-reports. Exit 0 on pass; exit 1 with a `FAIL:` line.
"""

from __future__ import annotations

import glob
import json
import os
import re
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

VOICE_AGENT = "uipath.agent.voice"
VOICE_TRIGGER = "core.trigger.voice"
CREATE_CALL = "uipath.conversational.voice.create-outgoing-call"
END_CALL = "uipath.conversational.voice.end-call"
MANUAL_TRIGGER = "core.trigger.manual"

# A node type that can own trigger-associated globals. Bindings sourced from
# anything else (a script or connector node's output) need no globals entry.
TRIGGER_PREFIXES = ("core.trigger.", "uipath.connector.trigger.")

# Generated/staging trees the CLI writes beside the sources. Python's glob
# already skips the dot-prefixed ones (`.cli-stage`, `.v1stage`,
# `.agent-builder`), but `_outputs` and `v1stage` are matched, and whether a
# staged copy sorts ahead of the real project depends on the project name.
# Same exclusion set the other maestro-flow checkers use.
EXCLUDED_PARTS = {
    ".agent-builder",
    ".cli-stage",
    ".v1stage",
    "_outputs",
    "node_modules",
    "v1stage",
}

# Lowercased, stripped placeholder prompts — same bar as `_shared/
# check_inline_agent.py`, which grades this for autonomous inline agents.
PLACEHOLDER_PROMPTS = {
    "",
    "you are an agentic assistant.",
    "you are an assistant.",
    "you are a helpful assistant.",
    "you are a voice agent.",
    "system prompt",
    "todo",
}
MIN_PROMPT_LEN = 40


def _fail(msg: str) -> int:
    print(f"FAIL: {msg}", file=sys.stderr)
    return 1


def _load_flow() -> tuple[str, dict]:
    """Return the (path, parsed) `.flow` that holds the voice agent node."""
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
        if any(n.get("type") == VOICE_AGENT for n in flow.get("nodes") or []):
            print(f"Reading {path}")
            return path, flow

    seen = sorted({str(n.get("type")) for _, f in parsed for n in f.get("nodes") or []})
    sys.exit(
        f"FAIL: no {VOICE_AGENT} node in any .flow under {project_dir}; "
        f"node types seen: {seen}"
    )


def _nodes_of(flow: dict, node_type: str) -> list[dict]:
    return [n for n in flow.get("nodes") or [] if n.get("type") == node_type]


JS_STRING_RE = re.compile(r"^=js:\s*(?P<expression>.+)$", re.S)


def _binding_expression(value: object) -> tuple[str | None, str | None]:
    """Return (expression, warning) for a callContext binding.

    The documented contract is a structured `{"type": "jsExpression",
    "expression": ...}` object — see `shared/node-output-wiring.md` and
    `inline-voice-agent/impl.md § The callContext wiring rule`. `type` IS graded:
    a `"literal"` object (the shape the create-call node's `to` field uses one
    section above in the doc, so an easy thing to copy by mistake) ships the
    expression text to the runtime and the call context never resolves.

    A bare `=js:` string carries the same expression and is accepted with a
    warning rather than a failure — it is off-contract, not inert. Any other
    string shape (`=jsonString:…`, an unprefixed expression) is a failure.
    """
    if isinstance(value, dict):
        binding_type = value.get("type")
        if binding_type != "jsExpression":
            return None, (
                f'binding object has type {binding_type!r}, not "jsExpression" — '
                f"only a jsExpression binding is evaluated; anything else ships "
                f"the expression to the runtime as text"
            )
        expression = value.get("expression")
        return (expression if isinstance(expression, str) else None), None
    if isinstance(value, str):
        match = JS_STRING_RE.match(value.strip())
        if not match:
            return None, (
                f"binding is the string {value.strip()[:80]!r} — the contract is a "
                f'{{"type": "jsExpression", "expression": …}} object'
            )
        return match.group("expression").strip(), (
            "binding is a `=js:` string; the persisted Studio Web shape is a "
            '{"type": "jsExpression", "expression": …} object'
        )
    return None, None


# Strict E.164: `+`, then 7-15 digits, no separators. Not a formatting
# preference — `impl.md` § Debug lists a malformed `to` as a cause of "outbound
# call never dials", so a number carrying dashes or spaces is a flow that does
# not place its call.
E164_RE = re.compile(r"^\+[1-9]\d{6,14}$")


def _is_e164(value: str) -> bool:
    return bool(E164_RE.match(value.strip()))


def _check_dial_fields(node: dict) -> list[str]:
    """`inputs.from` is a plain string, `inputs.to` a literal binding object.
    Both required, and the asymmetry is easy to get backwards. `fieldType` is
    not graded — the validator does not read it."""
    errors: list[str] = []
    inputs = node.get("inputs") or {}
    node_id = node.get("id")

    origin_from = inputs.get("from")
    if not isinstance(origin_from, str) or not origin_from.strip():
        errors.append(
            f"{CREATE_CALL} node {node_id!r} inputs.from is not a non-empty plain "
            f"string (the SIP trunk's E.164 number): {json.dumps(origin_from)[:120]}"
        )
    elif not _is_e164(origin_from):
        errors.append(
            f"{CREATE_CALL} node {node_id!r} inputs.from is not E.164 "
            f"(+ then 7-15 digits, no separators): {origin_from!r}"
        )

    origin_to = inputs.get("to")
    if not isinstance(origin_to, dict):
        errors.append(
            f"{CREATE_CALL} node {node_id!r} inputs.to is not a literal binding "
            f'object ({{"type": "literal", "expression": "<E164>"}}); `from` is the '
            f"plain string, `to` is the object: {json.dumps(origin_to)[:120]}"
        )
    else:
        destination = origin_to.get("expression")
        if not isinstance(destination, str) or not destination.strip():
            errors.append(
                f"{CREATE_CALL} node {node_id!r} inputs.to carries no expression: "
                f"{json.dumps(origin_to)[:120]}"
            )
        elif not _is_e164(destination):
            errors.append(
                f"{CREATE_CALL} node {node_id!r} inputs.to.expression is not E.164 "
                f"(+ then 7-15 digits, no separators): {destination!r}"
            )
    return errors


def check_call_context(flow: dict, origin_type: str = CREATE_CALL) -> int:
    """The callContext wiring rule: the origin node emits output.callContext and
    it must be bound into BOTH the voice agent and the end-call node.

    Outbound originates at create-outgoing-call, inbound at the trigger;
    everything downstream of the origin id is identical. The binding must be a
    `type: "jsExpression"` object (`fieldType` is NOT graded — the validator
    never reads it on a jsExpression); a `=js:` string passes with a warning.
    Outbound additionally grades the dial node's `from` / `to` fields.
    """
    origins = _nodes_of(flow, origin_type)
    if len(origins) != 1:
        return _fail(
            f"expected exactly 1 {origin_type} node (the call origin), "
            f"found {len(origins)}"
        )
    origin_id = origins[0].get("id")
    if not isinstance(origin_id, str) or not origin_id:
        return _fail(f"the {origin_type} node has no id")

    wanted = re.compile(
        r"\$vars\s*\.\s*" + re.escape(origin_id) + r"\s*\.\s*output\s*\.\s*callContext"
    )
    rules = {
        VOICE_AGENT: "conversational-voice-call-context",
        END_CALL: "conversational-voice-end-call-context",
    }

    errors: list[str] = []
    if origin_type == CREATE_CALL:
        errors.extend(_check_dial_fields(origins[0]))
        if not errors:
            print(f"OK      {CREATE_CALL} carries a plain-string from and a literal to")

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
        expression, warning = _binding_expression(raw)
        if not expression:
            errors.append(
                f"{node_type} node {node.get('id')!r} inputs.callContext "
                + (warning or "carries no expression")
                + f": {json.dumps(raw)[:200]}"
            )
            continue
        if warning:
            print(f"WARN    {node_type} node {node.get('id')!r}: {warning}")
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


def check_inbound_call_context(flow: dict) -> int:
    """Inbound topology: trigger-originated callContext, no dial-out node, no
    leftover manual trigger, and an entryPointId on the trigger (what a trunk
    binding resolves against)."""
    strays = _nodes_of(flow, MANUAL_TRIGGER)
    if strays:
        ids = ", ".join(repr(n.get("id")) for n in strays)
        return _fail(
            f"inbound flow still carries {len(strays)} {MANUAL_TRIGGER} node(s) "
            f"({ids}) — `flow init` scaffolds one, and adding the voice trigger "
            f"beside it ships a two-trigger flow. Delete the scaffolded trigger "
            f"and its edges when the flow starts from {VOICE_TRIGGER}"
        )

    dialers = _nodes_of(flow, CREATE_CALL)
    if dialers:
        ids = ", ".join(repr(n.get("id")) for n in dialers)
        return _fail(
            f"inbound flow must not dial out, but it has {len(dialers)} "
            f"{CREATE_CALL} node(s) ({ids}). An inbound flow starts from "
            f"{VOICE_TRIGGER} and the call already exists"
        )

    triggers = _nodes_of(flow, VOICE_TRIGGER)
    if len(triggers) != 1:
        return _fail(
            f"expected exactly 1 {VOICE_TRIGGER} node (the inbound trigger), "
            f"found {len(triggers)}"
        )
    entry_point = (triggers[0].get("inputs") or {}).get("entryPointId")
    if not isinstance(entry_point, str) or not entry_point.strip():
        return _fail(
            f"{VOICE_TRIGGER} node {triggers[0].get('id')!r} has no "
            f"inputs.entryPointId — a trunk binding resolves against it at "
            f"deploy time"
        )
    print(f"OK      {VOICE_TRIGGER} carries inputs.entryPointId")
    print(f"OK      no {CREATE_CALL} node (correct for inbound)")
    print(f"OK      no leftover {MANUAL_TRIGGER} node")

    return check_call_context(flow, VOICE_TRIGGER)


CONVERSATIONAL_ENGINE = "conversational-v1"


def check_agent_voice(flow_path: str, flow: dict) -> int:
    """The sidecar agent.json carries settings.voice (which `uip agent init
    --inline-in-flow --conversational` does NOT scaffold), keeps the
    conversational engine, and holds a real system prompt.

    `settings.engine` is graded here because `flow validate` does NOT check it
    (it checks only `metadata.isConversational`): a clobbered engine passes
    every other criterion and drops the call at runtime. The prompt is graded
    because an empty `messages[0].content` is legal — and a voice agent that
    cannot hold a conversation is not the deliverable.

    Topology independent; the agent dir is a UUID, so it is located through the
    voice node's inputs.source.
    """
    resolved = _voice_agent_json(flow_path, flow)
    if isinstance(resolved, int):
        return resolved
    _node, agent, agent_json = resolved

    errors: list[str] = []
    settings = agent.get("settings") or {}

    voice = settings.get("voice")
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

    engine = settings.get("engine")
    if engine != CONVERSATIONAL_ENGINE:
        errors.append(
            f"settings.engine is {engine!r}, not {CONVERSATIONAL_ENGINE!r} — "
            f"`flow validate` does not check it, so a clobbered engine ships and "
            f"surfaces only as a failed call. Leave the scaffolded value in place"
        )
    else:
        print(f"OK      settings.engine = {CONVERSATIONAL_ENGINE!r}")

    if (agent.get("metadata") or {}).get("isConversational") is not True:
        errors.append(
            "metadata.isConversational is not true — the agent was scaffolded "
            "without --conversational"
        )
    else:
        print("OK      metadata.isConversational is true")

    errors.extend(_prompt_errors(agent, agent_json))

    if errors:
        return _fail("; ".join(errors))
    return 0


def _prompt_errors(agent: dict, agent_json: str) -> list[str]:
    """The voice agent's system prompt has to be a real prompt. Same bar as
    `_shared/check_inline_agent.py` applies to autonomous inline agents."""
    system = [
        message.get("content") or ""
        for message in agent.get("messages") or []
        if isinstance(message, dict) and message.get("role") == "system"
    ]
    prompt = (system[0] if system else "").strip()
    if prompt.lower() in PLACEHOLDER_PROMPTS or len(prompt) < MIN_PROMPT_LEN:
        return [
            f"{agent_json} has no real system prompt (got {prompt[:60]!r}, "
            f"{len(prompt)} chars; the bar is {MIN_PROMPT_LEN}) — an empty prompt "
            f"is legal but the call then has no persona or goal to hold a "
            f"conversation with"
        ]
    print(f"OK      system prompt is {len(prompt)} chars")
    return []


def _voice_agent_json(flow_path: str, flow: dict) -> tuple[dict, dict, str] | int:
    """Return (voice node, parsed agent.json, agent.json path) or a fail code."""
    agents = _nodes_of(flow, VOICE_AGENT)
    if len(agents) != 1:
        return _fail(f"expected exactly 1 {VOICE_AGENT} node, found {len(agents)}")
    node = agents[0]
    source = (node.get("inputs") or {}).get("source")
    if not isinstance(source, str) or not source:
        return _fail(
            f"{VOICE_AGENT} node {node.get('id')!r} has no inputs.source "
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
            return node, json.load(handle), agent_json
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as err:
        return _fail(f"could not read {agent_json}: {err}")


BINDING_RE = re.compile(r"^=(?:js:)?\s*\$vars\.([A-Za-z0-9_-]+)\.output\.(.+)$")
INPUT_TOKEN_RE = re.compile(r"\{\{\s*input\.([A-Za-z0-9_]+)\s*\}\}")


def check_prompt_inputs(flow_path: str, flow: dict, min_inputs: int = 1) -> int:
    """Flow data reaching the voice prompt needs these pieces aligned:

    Delivery   node `inputs.agentInputVariables[]` binding -> BPMN JobArguments
    Contract   the same key under agent.json `inputSchema.properties`
    Resolution `{{input.<key>}}` in `messages[].content`
    Variable   a binding sourced from a TRIGGER also needs its
               `$vars.<trigger>.output.<id>` declared in `variables.globals[]`

    `impl.md` step 4 names a fifth piece, `messages[].contentTokens[]`. It is a
    pure derivation of `content` (`uip agent refresh` regenerates it and the doc
    forbids hand-authoring), so it is not graded structurally here — the task's
    advisory `agent refresh` criterion records it instead.

    Delivery is the piece that only `flow pack` reads: omit it and `flow debug`
    still back-fills from `inputSchema`, so the published call is the first place
    the input goes missing. A bare `$vars.…` left in prompt text is graded as a
    failure — nothing rewrites agent.json prompts, so it reaches the model raw.

    `min_inputs` is how many DISTINCT inputs the prompt must read. A task that
    asks for two values (name AND amount) passes its four-piece contract with
    one wired input unless the count is asserted — the second value silently
    goes ungraded.
    """
    resolved = _voice_agent_json(flow_path, flow)
    if isinstance(resolved, int):
        return resolved
    node, agent, agent_json = resolved

    errors: list[str] = []

    delivery = (node.get("inputs") or {}).get("agentInputVariables")
    if not isinstance(delivery, list) or not delivery:
        return _fail(
            f"{VOICE_AGENT} node {node.get('id')!r} has no inputs."
            f"agentInputVariables[] — that binding is what `flow pack` turns into "
            f"the runtime JobArguments, so the prompt's inputs would ship empty"
        )

    bound: dict[str, str] = {}
    for entry in delivery:
        if not isinstance(entry, dict):
            errors.append(f"agentInputVariables entry is not an object: {entry!r}")
            continue
        key = entry.get("id")
        if not isinstance(key, str) or not key:
            errors.append(f"agentInputVariables entry has no id: {entry!r}")
            continue
        if "value" in entry and "binding" not in entry:
            errors.append(
                f"agentInputVariables entry {key!r} uses `value` instead of "
                f"`binding` — the converter only reads `binding`, so JobArguments "
                f"ship empty"
            )
            continue
        binding = entry.get("binding")
        if not isinstance(binding, str) or not BINDING_RE.match(binding.strip()):
            errors.append(
                f"agentInputVariables entry {key!r} binding is not a "
                f"`=$vars.<node>.output.<field>` expression: {binding!r}"
            )
            continue
        bound[key] = binding.strip()

    # Variable: a binding sourced from a TRIGGER needs a trigger-associated
    # global. A binding sourced from any other node reads that node's own
    # output and declares nothing — per inline-agent/impl.md, the globals rule
    # is scoped to "when the upstream node is a trigger".
    triggers = {
        node.get("id")
        for node in flow.get("nodes") or []
        if isinstance(node.get("type"), str)
        and node["type"].startswith(TRIGGER_PREFIXES)
    }
    globals_ = ((flow.get("variables") or {}).get("globals")) or []
    declared = {
        (g.get("triggerNodeId"), g.get("id"))
        for g in globals_
        if isinstance(g, dict) and g.get("direction") in ("in", "inout")
    }
    for key, binding in bound.items():
        match = BINDING_RE.match(binding)
        source, field = match.group(1), match.group(2)
        if source not in triggers:
            continue
        if (source, field) not in declared:
            errors.append(
                f"{key!r} binds $vars.{source}.output.{field} from trigger "
                f"{source!r} but no variables.globals entry declares it "
                f'(direction "in" or "inout", triggerNodeId {source!r}) — it '
                f"resolves to nothing at runtime"
            )

    # Contract: every delivered key declared in the agent's inputSchema.
    properties = ((agent.get("inputSchema") or {}).get("properties")) or {}
    for key in bound:
        if key not in properties:
            errors.append(
                f"{key!r} is bound on the node but absent from {agent_json} "
                f"inputSchema.properties — the runtime drops it"
            )

    # Resolution: prompt tokens reference declared keys, and carry no raw $vars.
    referenced: set[str] = set()
    for index, message in enumerate(agent.get("messages") or []):
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str) or not content:
            continue
        if "$vars." in content:
            errors.append(
                f"messages[{index}].content contains a raw `$vars.` reference — "
                f"nothing rewrites agent.json prompt text, so it reaches the model "
                f"literally; use {{{{input.<key>}}}} instead"
            )
        referenced.update(INPUT_TOKEN_RE.findall(content))

    if not referenced:
        errors.append(
            f"no {{{{input.<key>}}}} token in any {agent_json} messages[].content — "
            f"the prompt never reads the delivered input"
        )
    elif len(referenced) < min_inputs:
        errors.append(
            f"the prompt reads {len(referenced)} distinct input(s) "
            f"({', '.join(sorted(referenced))}) but this flow is started with "
            f"{min_inputs} — every value the caller supplies has to reach the "
            f"prompt, not just the first"
        )
    for key in sorted(referenced - set(properties)):
        errors.append(
            f"prompt references {{{{input.{key}}}}} but inputSchema.properties "
            f"has no {key!r} key"
        )
    for key in sorted(referenced - set(bound)):
        errors.append(
            f"prompt references {{{{input.{key}}}}} but the node binds no such "
            f"input — `flow debug` back-fills it, `flow pack` does not"
        )

    if errors:
        return _fail("; ".join(errors))

    for key in sorted(referenced):
        print(f"OK      {key} : node binding -> inputSchema -> {{{{input.{key}}}}}")
    return 0


CHECKS = ("call-context", "inbound-call-context", "agent-voice", "prompt-inputs")


def _usage() -> int:
    print(
        f"usage: check_voice_flow.py {{{'|'.join(CHECKS)}}} [--min-inputs N]",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in CHECKS:
        return _usage()
    check, rest = argv[0], argv[1:]

    # `--min-inputs N` applies to prompt-inputs only; the other checks take no
    # arguments, so a stray flag is a task-authoring error, not a soft default.
    min_inputs = 1
    if rest:
        if check != "prompt-inputs" or len(rest) != 2 or rest[0] != "--min-inputs":
            return _usage()
        try:
            min_inputs = int(rest[1])
        except ValueError:
            return _usage()
        if min_inputs < 1:
            return _usage()

    flow_path, flow = _load_flow()
    if check == "call-context":
        return check_call_context(flow)
    if check == "inbound-call-context":
        return check_inbound_call_context(flow)
    if check == "prompt-inputs":
        return check_prompt_inputs(flow_path, flow, min_inputs)
    return check_agent_voice(flow_path, flow)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
