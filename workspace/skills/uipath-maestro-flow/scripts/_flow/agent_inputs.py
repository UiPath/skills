"""Inline-agent input wiring: emit the three aligned artifacts, or check them three ways.

emit  — from `$vars.<node>.output.<field>[:type]` sources, print the flow node's
        agentInputVariables[] entries, the agent.json inputSchema properties, and the
        {{input.<key>}} prompt tokens. Flatten rule: $vars.<node>.output.<var> -> <node>__output__<var>.
check — compare agentInputVariables[] ids, inputSchema properties and the {{input.X}} tokens in
        messages[].content three ways, and verify each binding's source resolves in the flow.
`uip agent refresh` regenerates messages[].contentTokens from content; this script never emits them.
"""
import json
import re

from . import lib as fl

TOKEN = re.compile(r"\{\{\s*input\.([A-Za-z0-9_]+)\s*\}\}")
RAW_VARS_TOKEN = re.compile(r"\{\{\s*\$vars\.")
SOURCE_RE = re.compile(r"^\$vars\.([A-Za-z_][\w]*)\.output(?:\.([\w.]+))?$")


def flatten(source):
    m = SOURCE_RE.match(source)
    if not m:
        fl.die("source %r must look like $vars.<nodeId>.output[.<field>]" % source)
    node, field = m.group(1), m.group(2)
    key = "%s__output" % node
    if field:
        key += "__" + field.replace(".", "__")
    return key


def cmd_emit(args):
    inputs, schema, tokens = [], {}, []
    for spec in args.source:
        source, _, vtype = spec.partition(":")
        vtype = vtype or "string"
        key = flatten(source)
        inputs.append({
            "id": key,
            "type": vtype,
            "binding": "=%s" % source,
            "description": "Bound from %s" % source,
        })
        schema[key] = {"type": vtype, "description": "Bound from %s" % source}
        tokens.append("{{input.%s}}" % key)
    payload = {
        "flowNode": {"inputs": {"agentInputVariables": inputs}},
        "agentJson": {"inputSchema": {"type": "object", "properties": schema}},
        "promptTokens": tokens,
    }
    print(json.dumps(payload, indent=2))
    return 0


def _agent_node(flow, node_id):
    nodes = fl.node_map(flow)
    if node_id:
        if node_id not in nodes:
            fl.die("no node with id %r" % node_id)
        return nodes[node_id]
    candidates = [n for n in flow["nodes"] if n.get("type") == "uipath.agent.autonomous"]
    if len(candidates) != 1:
        fl.die("found %d uipath.agent.autonomous nodes; pass --node" % len(candidates))
    return candidates[0]


def cmd_check(args):
    flow = fl.load(args.flow)
    node = _agent_node(flow, args.node)
    nid = node.get("id")
    try:
        with open(args.agent_json) as fh:
            agent = json.load(fh)
    except FileNotFoundError:
        fl.die("agent.json not found: %s" % args.agent_json)
    out = []
    delivery = {}
    for entry in (node.get("inputs") or {}).get("agentInputVariables") or []:
        if not isinstance(entry, dict):
            continue
        key = entry.get("id")
        delivery[key] = entry
        if "binding" not in entry:
            out.append(fl.finding("error", "BINDING_MISSING",
                                  "agentInputVariables entry %r has no `binding`; a `value` entry is ignored by the "
                                  "converter and the agent receives empty input" % key, node=nid))
            continue
        binding = entry["binding"]
        if not isinstance(binding, str) or not binding.startswith("="):
            out.append(fl.finding("error", "BINDING_SHAPE", "binding %r must start with `=`" % binding, node=nid))
            continue
        source = binding[1:]
        m = SOURCE_RE.match(source)
        if not m:
            out.append(fl.finding("warning", "BINDING_SOURCE_SHAPE",
                                  "binding %r is not $vars.<nodeId>.output[.<field>]" % source, node=nid))
            continue
        src_node, field = m.group(1), m.group(2)
        nodes = fl.node_map(flow)
        if src_node not in nodes:
            out.append(fl.finding("error", "BINDING_SOURCE_UNKNOWN",
                                  "binding references node %r which does not exist in the flow" % src_node, node=nid))
        elif fl.is_trigger(nodes[src_node].get("type", "")) and field:
            globs = [v for v in flow["variables"]["globals"] if isinstance(v, dict)]
            declared = any(v.get("id") == field and v.get("direction") == "in"
                           and v.get("triggerNodeId") == src_node for v in globs)
            if not declared:
                out.append(fl.finding("error", "TRIGGER_INPUT_UNDECLARED",
                                      "%s is bound but there is no variables.globals entry {id: %r, direction: 'in', "
                                      "triggerNodeId: %r}; validate passes and debug faults with empty JobArguments"
                                      % (source, field, src_node), node=nid))
        expected = flatten(source)
        if key != expected:
            out.append(fl.finding("error", "FLATTEN_MISMATCH",
                                  "id %r does not match the flatten rule for %s (expected %r)" % (key, source, expected),
                                  node=nid))

    schema = ((agent.get("inputSchema") or {}).get("properties") or {})
    contract = set(schema)
    tokens = set()
    raw_token_msgs = []
    for i, msg in enumerate(agent.get("messages") or []):
        content = (msg or {}).get("content")
        if isinstance(content, str):
            tokens |= set(TOKEN.findall(content))
            if RAW_VARS_TOKEN.search(content):
                raw_token_msgs.append(i)
    for i in raw_token_msgs:
        out.append(fl.finding("error", "RAW_VARS_TOKEN",
                              "messages[%d].content uses {{ $vars.X }}; prompts use the flattened "
                              "{{input.<node>__output__<var>}} form" % i, path="agent.json"))

    for key in sorted(set(delivery) - contract):
        out.append(fl.finding("error", "MISSING_IN_SCHEMA",
                              "delivered by the flow node but absent from agent.json inputSchema.properties", node=key))
    for key in sorted(contract - set(delivery)):
        out.append(fl.finding("error", "MISSING_DELIVERY",
                              "declared in inputSchema but no agentInputVariables entry delivers it; validate passes, "
                              "debug sees empty input", node=key))
    for key in sorted(tokens - contract):
        out.append(fl.finding("error", "TOKEN_NOT_IN_SCHEMA",
                              "prompt token {{input.%s}} names a key that is not in inputSchema" % key, node=key))
    for key in sorted(contract - tokens):
        out.append(fl.finding("warning", "UNUSED_INPUT",
                              "declared and delivered but never referenced by a prompt token", node=key))
    for key in sorted(contract & set(delivery)):
        dtype = delivery[key].get("type")
        stype = (schema.get(key) or {}).get("type")
        if dtype and stype and dtype != stype:
            out.append(fl.finding("error", "TYPE_MISMATCH",
                                  "agentInputVariables type %r != inputSchema type %r; JobArguments are "
                                  "strict-validated before the model runs" % (dtype, stype), node=key))
    return fl.report(out, args.format, "agent-inputs")

