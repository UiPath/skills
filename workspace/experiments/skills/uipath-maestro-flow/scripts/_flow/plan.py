"""Plan applier: one ordered list of ops, applied in memory, written once.

Op vocabulary (JSON, `{"ops": [ ... ]}`), all ids must start with a letter:

  {"op":"add-node","id":..,"type":..,"typeVersion":..,"definitionFile":..,"label":..,"inputs":{..},"outputs":"auto|none|a,b"}
  {"op":"delete-node","id":..}
  {"op":"add-edge","source":..,"sourcePort":..,"target":..,"targetPort":..,"id":..}
  {"op":"delete-edge","id":..}   |   {"op":"delete-edge","source":..,"target":..,"sourcePort":..}
  {"op":"set-input","node":..,"key":"a.b.c","value":..}
  {"op":"add-variable","id":..,"direction":"in|out|inout","type":..,"subType":..,"default":..,"description":..,"triggerNodeId":..}
  {"op":"add-output-mapping","endNode":..,"var":..,"source":..}
  {"op":"add-variable-update","node":..,"variable":..,"expression":..}
  {"op":"insert-between","upstream":..,"downstream":..,"upstreamPort":..,"id":..,"type":..,...,"nodeTargetPort":"input","nodeSourcePort":"output"}
  {"op":"insert-decision","upstream":..,"upstreamPort":..,"id":..,"expression":..,"trueTarget":..,"falseTarget":..,"typeVersion":..,"definitionFile":..}
  {"op":"remove-reconnect","id":..}
  {"op":"replace-trigger-scheduled","node":..,"definitionFile":..,"timerType":"timeCycle","timerPreset":".."}
  {"op":"agent-inputs","node":..,"sources":["$vars.start.output.x:string", ..]}

Repair ops emitted by `audit_flow.py --fix-plan` (same schema, applied by the same applier):

  {"op":"add-node-variable","node":..,"outputId":"output"}
  {"op":"set-layout","node":..,"width":96,"height":96,"x":0,"y":0}
  {"op":"add-bindings","entries":[{..}]}
  {"op":"set-error-flag","node":..,"value":true|false}
"""
import json
import os
import re

from . import lib as fl

ID_RE = re.compile(r"^[A-Za-z]")
SOURCE_RE = re.compile(r"^\$vars\.([A-Za-z_][\w]*)\.output(?:\.([\w.]+))?$")


def _die(i, msg, code=2):
    fl.die("op %d (%s): %s" % (i, _CUR.get("op", "?"), msg), code)


_CUR = {}


def _check_id(i, kind, value):
    if not ID_RE.match(value or ""):
        _die(i, "%s id %r must start with a letter (XML NCName); never a bare UUID" % (kind, value))


def _definition(op, base_dir):
    path = op.get("definitionFile")
    if not path:
        return None
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    with open(path) as fh:
        return fl.unwrap_definition(json.load(fh))


def _skeleton_outputs(ntype, outputs):
    if fl.is_terminal(ntype) or not outputs:
        return {}
    if fl.is_trigger(ntype):
        return {"output": {"type": "object", "description": "Data passed when triggering the process.",
                           "source": "null", "var": "output"}}
    if fl.is_orch_job(ntype):
        return {"error": {"type": "object", "description": "Error information if the node fails.",
                          "source": "=Error", "var": "error"}}
    block = {}
    for out in outputs:
        if out == "error":
            block["error"] = {"type": "object", "description": "Error information if the node fails.",
                              "source": "=Error", "var": "error"}
        else:
            block[out] = {"type": "object", "description": "The return value of the node.",
                          "source": "=result.response", "var": out}
    return block


def _sync_node_variables(flow, nid, outputs):
    have = {v.get("id") for v in flow["variables"]["nodes"] if isinstance(v, dict)}
    added = 0
    for out in outputs:
        vid = "%s.%s" % (nid, out)
        if vid in have:
            continue
        flow["variables"]["nodes"].append(
            {"id": vid, "type": "object", "binding": {"nodeId": nid, "outputId": out}})
        added += 1
    return added


def _find_edge(flow, source, target, source_port=None):
    for e in flow["edges"]:
        if e.get("sourceNodeId") == source and e.get("targetNodeId") == target:
            if source_port is None or e.get("sourcePort") == source_port:
                return e
    return None


def flatten(source):
    m = SOURCE_RE.match(source)
    if not m:
        return None
    key = "%s__output" % m.group(1)
    if m.group(2):
        key += "__" + m.group(2).replace(".", "__")
    return key


# --- ops -------------------------------------------------------------------

def op_add_node(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    nid = op.get("id")
    ntype = op.get("type")
    if not nid or not ntype:
        _die(i, "add-node needs id and type")
    _check_id(i, "node", nid)
    if nid in nodes:
        _die(i, "node id %r already exists" % nid)
    if fl.is_cli_owned(ntype) and not op.get("allowCliOwned"):
        _die(i, "%s is CLI-owned: add it with `uip maestro flow node add` + `node configure`" % ntype, 3)
    definition = _definition(op, base_dir)
    version = op.get("typeVersion")
    if definition is not None:
        dver = definition.get("version")
        if version is None:
            version = dver
        elif dver is not None and str(dver) != str(version):
            _die(i, "typeVersion %r does not string-match the definition version %r" % (version, dver))
    if version is None:
        _die(i, "typeVersion is required when no definitionFile is given")
    node = {"id": nid, "type": ntype, "typeVersion": str(version),
            "display": {"label": op.get("label") or nid}, "inputs": op.get("inputs") or {}}
    spec = op.get("outputs", "auto")
    if spec == "auto":
        outputs = fl.declared_outputs(definition) if definition else []
        if not outputs and not fl.is_terminal(ntype):
            outputs = ["output"] if fl.is_trigger(ntype) else ["output", "error"]
    elif spec in ("none", None):
        outputs = []
    elif isinstance(spec, list):
        outputs = spec
    else:
        outputs = [o.strip() for o in str(spec).split(",") if o.strip()]
    block = _skeleton_outputs(ntype, outputs)
    if block:
        node["outputs"] = block
    flow["nodes"].append(node)
    notes = []
    if definition is not None and fl.definition_for(flow, node) is None:
        flow["definitions"].append(definition)
        notes.append("definition added")
    if not fl.is_terminal(ntype):
        n = _sync_node_variables(flow, nid, outputs)
        if n:
            notes.append("variables.nodes +%d" % n)
    if ntype != "stickyNote":
        flow["layout"]["nodes"].setdefault(
            nid, {"position": {"x": 0, "y": 0}, "size": fl.expected_size(ntype), "collapsed": False})
    return "add-node %s (%s v%s)%s" % (nid, ntype, version, ("; " + ", ".join(notes)) if notes else "")


def op_delete_node(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    nid = op.get("id")
    if nid not in nodes:
        _die(i, "no node with id %r" % nid)
    node = nodes[nid]
    flow["nodes"] = [n for n in flow["nodes"] if n.get("id") != nid]
    dropped = [e for e in flow["edges"] if nid in (e.get("sourceNodeId"), e.get("targetNodeId"))]
    flow["edges"] = [e for e in flow["edges"] if e not in dropped]
    flow["variables"]["nodes"] = [v for v in flow["variables"]["nodes"]
                                  if not (isinstance(v, dict) and (v.get("binding") or {}).get("nodeId") == nid)]
    updates = flow["variables"].get("variableUpdates")
    if isinstance(updates, dict):
        updates.pop(nid, None)
    flow["layout"]["nodes"].pop(nid, None)
    pruned = ""
    if not any(n.get("type") == node.get("type") for n in flow["nodes"]):
        before = len(flow["definitions"])
        flow["definitions"] = [d for d in flow["definitions"]
                               if (d.get("nodeType") or d.get("type")) != node.get("type")]
        if len(flow["definitions"]) < before:
            pruned = "; definition pruned"
    extra = ""
    if node.get("type", "").startswith("uipath.connector."):
        extra = "; check bindings_v2.json only if no other node uses that connector"
    return "delete-node %s; edges -%d%s%s" % (nid, len(dropped), pruned, extra)


def op_add_edge(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    src, tgt = op.get("source"), op.get("target")
    sp, tp = op.get("sourcePort"), op.get("targetPort")
    if not tp:
        _die(i, "targetPort is required on every edge; validate rejects edges without it")
    if not sp:
        _die(i, "sourcePort is required (the field is sourcePort, never sourceHandle)")
    for role, nid in (("source", src), ("target", tgt)):
        if nid not in nodes:
            _die(i, "%s node %r does not exist" % (role, nid))
    eid = op.get("id") or "edge_%s_%s_%s_%s" % (src, sp, tgt, tp)
    _check_id(i, "edge", eid)
    if any(e.get("id") == eid for e in flow["edges"]):
        _die(i, "edge id %r already exists" % eid)
    flow["edges"].append({"id": eid, "sourceNodeId": src, "sourcePort": sp,
                          "targetNodeId": tgt, "targetPort": tp})
    flagged = ""
    if sp == "error":
        nodes[src].setdefault("inputs", {})["errorHandlingEnabled"] = True
        flagged = "; errorHandlingEnabled set on %s" % src
    return "add-edge %s%s" % (eid, flagged)


def op_delete_edge(flow, op, i, base_dir):
    if op.get("id"):
        keep = [e for e in flow["edges"] if e.get("id") != op["id"]]
    elif op.get("source") and op.get("target"):
        keep = [e for e in flow["edges"]
                if not (e.get("sourceNodeId") == op["source"] and e.get("targetNodeId") == op["target"]
                        and (op.get("sourcePort") is None or e.get("sourcePort") == op["sourcePort"]))]
    else:
        _die(i, "delete-edge needs id, or source and target")
    removed = len(flow["edges"]) - len(keep)
    if removed == 0:
        _die(i, "no matching edge found")
    flow["edges"] = keep
    return "delete-edge ×%d" % removed


def op_set_input(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    nid = op.get("node")
    if nid not in nodes:
        _die(i, "no node with id %r" % nid)
    node = nodes[nid]
    key = op.get("key") or ""
    if not key:
        _die(i, "set-input needs key")
    if fl.is_cli_owned(node.get("type", "")) and key.split(".")[0] == "detail" and not op.get("allowCliOwned"):
        _die(i, "inputs.detail on %s is CLI-owned: use `uip maestro flow node configure --detail`" % node.get("type"), 3)
    target = node.setdefault("inputs", {})
    parts = key.split(".")
    for p in parts[:-1]:
        nxt = target.get(p)
        if not isinstance(nxt, dict):
            nxt = {}
            target[p] = nxt
        target = nxt
    target[parts[-1]] = op.get("value")
    return "set-input inputs.%s on %s" % (key, nid)


def op_add_variable(flow, op, i, base_dir):
    globs = flow["variables"]["globals"]
    vid = op.get("id")
    if not vid or op.get("direction") not in ("in", "out", "inout"):
        _die(i, "add-variable needs id and direction in|out|inout")
    if any(isinstance(v, dict) and v.get("id") == vid for v in globs):
        _die(i, "variable %r already declared" % vid)
    var = {"id": vid, "direction": op["direction"], "type": op.get("type", "string")}
    for src, dst in (("subType", "subType"), ("default", "defaultValue"),
                     ("description", "description"), ("triggerNodeId", "triggerNodeId")):
        if op.get(src) is not None:
            var[dst] = op[src]
    globs.append(var)
    hint = "; map it on every reachable End node" if op["direction"] == "out" else ""
    return "add-variable %s (%s)%s" % (vid, op["direction"], hint)


def op_add_output_mapping(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    nid = op.get("endNode")
    if nid not in nodes:
        _die(i, "no node with id %r" % nid)
    if not fl.is_terminal(nodes[nid].get("type", "")):
        _die(i, "%s is %s, not an End/terminate node" % (nid, nodes[nid].get("type")))
    if not op.get("var") or op.get("source") is None:
        _die(i, "add-output-mapping needs var and source")
    nodes[nid].setdefault("outputs", {})[op["var"]] = {"source": op["source"]}
    return "add-output-mapping %s on %s" % (op["var"], nid)


def op_add_variable_update(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    nid = op.get("node")
    if nid not in nodes:
        _die(i, "no node with id %r" % nid)
    declared = {v.get("id"): v for v in flow["variables"]["globals"] if isinstance(v, dict)}
    var = declared.get(op.get("variable"))
    if var is None:
        _die(i, "variable %r is not declared in variables.globals" % op.get("variable"))
    if var.get("direction") != "inout":
        _die(i, "only inout variables can be updated; %r is %r" % (op["variable"], var.get("direction")))
    flow["variables"].setdefault("variableUpdates", {}).setdefault(nid, []).append(
        {"variableId": op["variable"], "expression": op.get("expression")})
    return "add-variable-update %s on %s" % (op["variable"], nid)


def op_insert_between(flow, op, i, base_dir):
    edge = _find_edge(flow, op.get("upstream"), op.get("downstream"), op.get("upstreamPort"))
    if edge is None:
        _die(i, "no edge %s -> %s to split" % (op.get("upstream"), op.get("downstream")))
    up_port, down_port = edge.get("sourcePort"), edge.get("targetPort")
    out = [op_delete_edge(flow, {"id": edge["id"]}, i, base_dir),
           op_add_node(flow, op, i, base_dir),
           op_add_edge(flow, {"source": op["upstream"], "sourcePort": up_port, "target": op["id"],
                              "targetPort": op.get("nodeTargetPort", "input")}, i, base_dir),
           op_add_edge(flow, {"source": op["id"], "sourcePort": op.get("nodeSourcePort", "output"),
                              "target": op["downstream"], "targetPort": down_port}, i, base_dir)]
    return "insert-between %s (%s -> %s)" % (op["id"], op["upstream"], op["downstream"])


def op_insert_decision(flow, op, i, base_dir):
    edge = _find_edge(flow, op.get("upstream"), op.get("trueTarget"), op.get("upstreamPort"))
    if edge is None:
        edge = next((e for e in flow["edges"] if e.get("sourceNodeId") == op.get("upstream")
                     and (op.get("upstreamPort") is None or e.get("sourcePort") == op["upstreamPort"])), None)
    if edge is None:
        _die(i, "no outgoing edge from %s to replace with the branch" % op.get("upstream"))
    up_port = edge.get("sourcePort")
    op_delete_edge(flow, {"id": edge["id"]}, i, base_dir)
    node_op = dict(op)
    node_op.update({"type": "core.logic.decision", "outputs": "none",
                    "inputs": {"expression": op.get("expression")}})
    op_add_node(flow, node_op, i, base_dir)
    op_add_edge(flow, {"source": op["upstream"], "sourcePort": up_port, "target": op["id"],
                       "targetPort": "input"}, i, base_dir)
    for port, target in (("true", op.get("trueTarget")), ("false", op.get("falseTarget"))):
        if not target:
            _die(i, "insert-decision needs trueTarget and falseTarget")
        op_add_edge(flow, {"source": op["id"], "sourcePort": port, "target": target,
                           "targetPort": "input"}, i, base_dir)
    return "insert-decision %s after %s (true -> %s, false -> %s)" % (
        op["id"], op["upstream"], op["trueTarget"], op["falseTarget"])


def op_remove_reconnect(flow, op, i, base_dir):
    nid = op.get("id")
    nodes = fl.node_map(flow)
    if nid not in nodes:
        _die(i, "no node with id %r" % nid)
    incoming = [e for e in fl.in_edges(flow, nid) if e.get("sourcePort") != "error"]
    outgoing = [e for e in fl.out_edges(flow, nid) if e.get("sourcePort") != "error"]
    if not incoming or not outgoing:
        _die(i, "cannot reconnect: %s has %d non-error incoming and %d non-error outgoing edge(s)"
             % (nid, len(incoming), len(outgoing)))
    up, down = incoming[0], outgoing[0]
    op_delete_node(flow, {"id": nid}, i, base_dir)
    op_add_edge(flow, {"source": up["sourceNodeId"], "sourcePort": up["sourcePort"],
                       "target": down["targetNodeId"], "targetPort": down["targetPort"]}, i, base_dir)
    extra = (len(incoming) - 1) + (len(outgoing) - 1)
    return "remove-reconnect %s (%s -> %s)%s" % (
        nid, up["sourceNodeId"], down["targetNodeId"],
        "; %d other edge(s) dropped, rewire if needed" % extra if extra else "")


def op_replace_trigger_scheduled(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    nid = op.get("node")
    node = nodes.get(nid)
    if node is None:
        _die(i, "no node with id %r" % nid)
    if node.get("type") != "core.trigger.manual":
        _die(i, "%s is %s, expected core.trigger.manual" % (nid, node.get("type")))
    definition = _definition(op, base_dir)
    if definition is None:
        _die(i, "replace-trigger-scheduled needs definitionFile for core.trigger.scheduled")
    if (definition.get("nodeType") or definition.get("type")) != "core.trigger.scheduled":
        _die(i, "definitionFile is for %s, expected core.trigger.scheduled"
             % (definition.get("nodeType") or definition.get("type")))
    node["type"] = "core.trigger.scheduled"
    if definition.get("version"):
        node["typeVersion"] = str(definition["version"])
    inputs = node.setdefault("inputs", {})
    inputs["timerType"] = op.get("timerType", "timeCycle")
    if not op.get("timerPreset"):
        _die(i, "replace-trigger-scheduled needs timerPreset (e.g. R/PT1H)")
    inputs["timerPreset"] = op["timerPreset"]
    flow["definitions"] = [d for d in flow["definitions"]
                           if (d.get("nodeType") or d.get("type")) != "core.trigger.manual"]
    if fl.definition_for(flow, node) is None:
        flow["definitions"].append(definition)
    return "replace-trigger-scheduled %s (%s, %s)" % (nid, inputs["timerType"], inputs["timerPreset"])


def op_agent_inputs(flow, op, i, base_dir):
    nodes = fl.node_map(flow)
    nid = op.get("node")
    if nid not in nodes:
        _die(i, "no node with id %r" % nid)
    entries = []
    for spec in op.get("sources") or []:
        source, _, vtype = str(spec).partition(":")
        key = flatten(source)
        if key is None:
            _die(i, "source %r must look like $vars.<nodeId>.output[.<field>]" % source)
        entries.append({"id": key, "type": vtype or "string", "binding": "=%s" % source,
                        "description": "Bound from %s" % source})
    if not entries:
        _die(i, "agent-inputs needs a non-empty sources list")
    nodes[nid].setdefault("inputs", {})["agentInputVariables"] = entries
    return "agent-inputs %s (%d binding(s): %s)" % (nid, len(entries), ", ".join(e["id"] for e in entries))


# --- repair ops (emitted by audit_flow --fix-plan) -------------------------

def op_add_node_variable(flow, op, i, base_dir):
    nid, out = op.get("node"), op.get("outputId", "output")
    if nid not in fl.node_map(flow):
        _die(i, "no node with id %r" % nid)
    n = _sync_node_variables(flow, nid, [out])
    return "add-node-variable %s.%s%s" % (nid, out, "" if n else " (already present)")


def op_set_layout(flow, op, i, base_dir):
    nid = op.get("node")
    if nid not in fl.node_map(flow):
        _die(i, "no node with id %r" % nid)
    entry = flow["layout"]["nodes"].setdefault(nid, {"position": {"x": 0, "y": 0}, "collapsed": False})
    entry.setdefault("position", {"x": op.get("x", 0), "y": op.get("y", 0)})
    entry["size"] = {"width": op.get("width"), "height": op.get("height")}
    entry.setdefault("collapsed", False)
    return "set-layout %s (%sx%s)" % (nid, op.get("width"), op.get("height"))


def op_add_bindings(flow, op, i, base_dir):
    entries = op.get("entries") or []
    if not entries:
        _die(i, "add-bindings needs entries")
    have = {(b.get("resourceKey"), b.get("name")) for b in (flow.get("bindings") or []) if isinstance(b, dict)}
    added = 0
    for e in entries:
        if (e.get("resourceKey"), e.get("name")) in have:
            continue
        flow.setdefault("bindings", []).append(e)
        added += 1
    return "add-bindings +%d" % added


def op_set_error_flag(flow, op, i, base_dir):
    nid = op.get("node")
    nodes = fl.node_map(flow)
    if nid not in nodes:
        _die(i, "no node with id %r" % nid)
    inputs = nodes[nid].setdefault("inputs", {})
    if op.get("value"):
        inputs["errorHandlingEnabled"] = True
        return "set-error-flag %s = true" % nid
    inputs.pop("errorHandlingEnabled", None)
    return "set-error-flag %s removed" % nid


OPS = {
    "add-node": op_add_node,
    "delete-node": op_delete_node,
    "add-edge": op_add_edge,
    "delete-edge": op_delete_edge,
    "set-input": op_set_input,
    "add-variable": op_add_variable,
    "add-output-mapping": op_add_output_mapping,
    "add-variable-update": op_add_variable_update,
    "insert-between": op_insert_between,
    "insert-decision": op_insert_decision,
    "remove-reconnect": op_remove_reconnect,
    "replace-trigger-scheduled": op_replace_trigger_scheduled,
    "agent-inputs": op_agent_inputs,
    "add-node-variable": op_add_node_variable,
    "set-layout": op_set_layout,
    "add-bindings": op_add_bindings,
    "set-error-flag": op_set_error_flag,
}


def load_plan(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except FileNotFoundError:
        fl.die("plan file not found: %s" % path)
    except json.JSONDecodeError as exc:
        fl.die("%s is not valid JSON: %s" % (path, exc))
    ops = data.get("ops") if isinstance(data, dict) else data
    if not isinstance(ops, list) or not ops:
        fl.die("plan must hold a non-empty \"ops\" array")
    for i, op in enumerate(ops, 1):
        if not isinstance(op, dict) or op.get("op") not in OPS:
            fl.die("op %d: unknown op %r (known: %s)" % (i, (op or {}).get("op"), ", ".join(sorted(OPS))))
    return ops


def apply_ops(flow, ops, base_dir="."):
    """Apply every op in order against the in-memory flow. Raises SystemExit on the first failure."""
    log = []
    for i, op in enumerate(ops, 1):
        _CUR.clear()
        _CUR.update(op)
        log.append(OPS[op["op"]](flow, op, i, base_dir))
    return log
