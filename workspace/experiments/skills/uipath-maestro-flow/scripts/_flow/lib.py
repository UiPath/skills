"""Loader, graph helpers and finding/report helpers for `.flow` JSON."""
import json
import sys

TRIGGER_TYPES = {"core.trigger.manual", "core.trigger.scheduled"}
TRIGGER_PREFIXES = ("uipath.connector.trigger.",)
TERMINAL_TYPES = {"core.control.end", "core.logic.terminate"}
CLI_OWNED_PREFIXES = ("uipath.connector.trigger.", "uipath.connector.event.", "uipath.connector.")
CLI_OWNED_TYPES = {"core.action.http.v2"}
RESOURCE_PREFIXES = (
    "uipath.core.rpa-workflow.",
    "uipath.core.agent.",
    "uipath.core.flow.",
    "uipath.core.agentic-process.",
    "uipath.core.api-workflow.",
    "uipath.core.human-task.",
)


def die(msg, code=2):
    sys.stderr.write("error: %s\n" % msg)
    raise SystemExit(code)


def load(path):
    try:
        with open(path) as fh:
            data = json.load(fh)
    except FileNotFoundError:
        die("flow file not found: %s" % path)
    except json.JSONDecodeError as exc:
        die("%s is not valid JSON: %s" % (path, exc))
    if not isinstance(data, dict):
        die("%s does not contain a flow object" % path)
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    data.setdefault("definitions", [])
    data.setdefault("variables", {})
    data["variables"].setdefault("globals", [])
    data["variables"].setdefault("nodes", [])
    data.setdefault("layout", {})
    data["layout"].setdefault("nodes", {})
    return data


def save(path, flow):
    with open(path, "w") as fh:
        json.dump(flow, fh, indent=2)
        fh.write("\n")


def node_map(flow):
    return {n["id"]: n for n in flow["nodes"] if isinstance(n, dict) and "id" in n}


def is_trigger(ntype):
    return ntype in TRIGGER_TYPES or ntype.startswith(TRIGGER_PREFIXES)


def is_terminal(ntype):
    return ntype in TERMINAL_TYPES


def is_cli_owned(ntype):
    if ntype in CLI_OWNED_TYPES:
        return True
    return ntype.startswith(CLI_OWNED_PREFIXES)


def is_resource_node(ntype):
    return ntype.startswith(RESOURCE_PREFIXES)


def out_edges(flow, nid, port=None):
    return [
        e for e in flow["edges"]
        if e.get("sourceNodeId") == nid and (port is None or e.get("sourcePort") == port)
    ]


def in_edges(flow, nid):
    return [e for e in flow["edges"] if e.get("targetNodeId") == nid]


def definition_for(flow, node):
    want_type = node.get("type")
    want_version = node.get("typeVersion")
    for d in flow["definitions"]:
        if not isinstance(d, dict):
            continue
        dtype = d.get("nodeType") or d.get("type")
        if dtype != want_type:
            continue
        if want_version is None or d.get("version") in (None, want_version):
            return d
    return None


def unwrap_definition(payload):
    """Accept `registry get` output (Data.Node), a bare Data object, or the node manifest itself."""
    if not isinstance(payload, dict):
        die("definition payload must be a JSON object")
    for path in (("Data", "Node"), ("Data",), ("Node",)):
        cur = payload
        ok = True
        for key in path:
            if isinstance(cur, dict) and key in cur:
                cur = cur[key]
            else:
                ok = False
                break
        if ok and isinstance(cur, dict) and (cur.get("nodeType") or cur.get("type")):
            return cur
    if payload.get("nodeType") or payload.get("type"):
        return payload
    die("could not locate a node definition in the payload (looked at Data.Node, Data, Node, top level)")


def declared_outputs(definition):
    """Output ids the manifest declares, sorted for determinism."""
    if not isinstance(definition, dict):
        return []
    outdef = definition.get("outputDefinition") or {}
    if isinstance(outdef, dict):
        props = outdef.get("properties") if isinstance(outdef.get("properties"), dict) else outdef
        if isinstance(props, dict) and props:
            return sorted(k for k in props if isinstance(k, str))
    return []


def terminals_from(flow, start, seen=None):
    """End/terminate nodes reachable from `start` following non-error ports."""
    seen = set() if seen is None else seen
    if start in seen:
        return set()
    seen.add(start)
    nodes = node_map(flow)
    if is_terminal((nodes.get(start) or {}).get("type", "")):
        return {start}
    found = set()
    for e in flow["edges"]:
        if e.get("sourceNodeId") == start and e.get("sourcePort") != "error":
            found |= terminals_from(flow, e.get("targetNodeId"), seen)
    return found


def finding(severity, code, message, node=None, edge=None, path=None):
    item = {"severity": severity, "code": code, "message": message}
    if node:
        item["node"] = node
    if edge:
        item["edge"] = edge
    if path:
        item["path"] = path
    return item


def location(f):
    parts = [f.get("node") or f.get("edge") or ""]
    if f.get("path"):
        parts.append(f["path"])
    return ":".join(x for x in parts if x) or "-"


def report(findings, fmt, title):
    findings = sorted(findings, key=lambda f: (f["severity"] != "error", f["code"], f.get("node") or "", f.get("path") or "", f["message"]))
    if fmt == "json":
        print(json.dumps({"title": title, "findings": findings}, indent=2))
    else:
        for f in findings:
            print("%-7s %-26s %-46s %s" % (f["severity"], f["code"], location(f), f["message"]))
        errs = sum(1 for f in findings if f["severity"] == "error")
        warns = len(findings) - errs
        print("%s: %d error(s), %d warning(s)" % (title, errs, warns))
    return 1 if any(f["severity"] == "error" for f in findings) else 0


INLINE_AGENT_TYPES = {"uipath.agent.autonomous", "uipath.agent.conversational"}
CONTAINER_TYPES = {"core.logic.loop", "core.logic.group"}
ORCH_JOB_PREFIXES = (
    "uipath.core.api-workflow.",
    "uipath.core.rpa-workflow.",
    "uipath.core.agent.",
    "uipath.core.agentic-process.",
    "uipath.core.function.",
)


def expected_size(ntype):
    """Canvas size `flow format` assigns, by node shape."""
    if ntype in INLINE_AGENT_TYPES:
        return {"width": 288, "height": 96}
    if ntype in CONTAINER_TYPES:
        return {"width": 560, "height": 320}
    return {"width": 96, "height": 96}


def is_orch_job(ntype):
    return ntype.startswith(ORCH_JOB_PREFIXES)
