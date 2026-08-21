"""Check the `.flow` conditions that `uip maestro flow validate` does not catch.

Covers: inputs.errorHandlingEnabled with no error edge, error paths that rejoin the happy path or
share a success terminal, layout sizes that disagree with a node's canvas shape, missing
variables.nodes[] entries, an unwired HITL completion port, ids that do not start with a letter,
and out variables not mapped on every reachable End node.
"""
import re

from . import lib as fl

ID_RE = re.compile(r"^[A-Za-z]")
HITL_PORTS = ("completed", "outcome-completed")
REFERENCE_HINT = re.compile(r"(^|[^A-Za-z])(id|ids|key|channel|folder|project|sheet|mailbox)", re.I)


def collect(flow, reference_fields=False):
    out = []
    nodes = fl.node_map(flow)

    for nid, node in sorted(nodes.items()):
        if not ID_RE.match(nid or ""):
            out.append(fl.finding("error", "BAD_NODE_ID",
                                  "node id must start with a letter (XML NCName); the engine drops the reference "
                                  "and the run completes having executed only the start node", node=nid))
    for e in flow["edges"]:
        eid = e.get("id") or ""
        if not ID_RE.match(eid):
            out.append(fl.finding("error", "BAD_EDGE_ID",
                                  "edge id must start with a letter; validate passes but the engine cannot traverse",
                                  edge=eid or "<no id>"))

    for nid, node in sorted(nodes.items()):
        ntype = node.get("type", "")
        flagged = (node.get("inputs") or {}).get("errorHandlingEnabled") is True
        err_edges = fl.out_edges(flow, nid, "error")
        ok_edges = [e for e in fl.out_edges(flow, nid) if e.get("sourcePort") != "error"]
        if flagged and not err_edges:
            out.append(fl.finding("error", "FLAG_WITHOUT_ERROR_EDGE",
                                  "inputs.errorHandlingEnabled is set with no error edge; the fault is swallowed "
                                  "and the run reports success", node=nid))
        if err_edges and not flagged:
            out.append(fl.finding("error", "ERROR_EDGE_WITHOUT_FLAG",
                                  "error edge present but inputs.errorHandlingEnabled is not true", node=nid))
        if err_edges:
            ok_targets = {e.get("targetNodeId") for e in ok_edges}
            ok_terms = set()
            for t in sorted(ok_targets):
                ok_terms |= fl.terminals_from(flow, t)
            for e in err_edges:
                target = e.get("targetNodeId")
                if target in ok_targets:
                    out.append(fl.finding("error", "ERROR_REJOINS_HAPPY_PATH",
                                          "error -> %s is also on the happy path; every failure would report success"
                                          % target, node=nid, edge=e.get("id")))
                    continue
                err_terms = fl.terminals_from(flow, target)
                if err_terms and ok_terms and err_terms <= ok_terms:
                    out.append(fl.finding("error", "ERROR_SHARES_SUCCESS_TERMINAL",
                                          "error -> %s reaches only the success terminal(s) %s; send it to a distinct "
                                          "End node or core.logic.terminate"
                                          % (target, ", ".join(sorted(err_terms))), node=nid, edge=e.get("id")))

    for nid, node in sorted(nodes.items()):
        ntype = node.get("type", "")
        if ntype == "stickyNote":
            continue
        entry = flow["layout"]["nodes"].get(nid)
        if entry is None:
            out.append(fl.finding("warning", "MISSING_LAYOUT",
                                  "no layout.nodes entry; run `uip maestro flow format`", node=nid))
            continue
        want = fl.expected_size(ntype)
        got = entry.get("size") or {}
        if (got.get("width"), got.get("height")) != (want["width"], want["height"]):
            out.append(fl.finding("warning", "LAYOUT_SIZE_MISMATCH",
                                  "size %sx%s disagrees with this node's shape (%sx%s); Studio Web renders it "
                                  "misshapen until `flow format` runs"
                                  % (got.get("width"), got.get("height"), want["width"], want["height"]), node=nid))

    declared = {v.get("id") for v in flow["variables"]["nodes"] if isinstance(v, dict)}
    for nid, node in sorted(nodes.items()):
        ntype = node.get("type", "")
        if fl.is_terminal(ntype):
            continue
        outputs = sorted((node.get("outputs") or {}).keys())
        if not outputs:
            outputs = fl.declared_outputs(fl.definition_for(flow, node))
        if not outputs:
            # nothing declares an output (control-flow nodes such as decision/switch/merge, or a
            # node whose definition carries no outputDefinition) — there is nothing to bind.
            continue
        consumed = "%s.output" % nid
        if "output" in outputs and consumed not in declared:
            out.append(fl.finding("error", "MISSING_NODE_VARIABLE",
                                  "no variables.nodes[] entry %r; $vars.%s.output resolves to undefined at runtime "
                                  "even though validate passes. `uip maestro flow format` regenerates it"
                                  % (consumed, nid), node=nid))

    for nid, node in sorted(nodes.items()):
        if node.get("type") != "uipath.human-in-the-loop.quick-form":
            continue
        if not any(e.get("sourcePort") in HITL_PORTS for e in fl.out_edges(flow, nid)):
            out.append(fl.finding("error", "HITL_PORT_UNWIRED",
                                  "no outgoing edge from the completion port (%s); the flow blocks indefinitely "
                                  "after the human task completes" % " / ".join(HITL_PORTS), node=nid))

    ends = [n for n in flow["nodes"] if fl.is_terminal(n.get("type", ""))]
    reachable_ends = set()
    for nid, node in nodes.items():
        if fl.is_trigger(node.get("type", "")):
            reachable_ends |= fl.terminals_from(flow, nid)
    outs = [v.get("id") for v in flow["variables"]["globals"]
            if isinstance(v, dict) and v.get("direction") == "out"]
    for end in ends:
        eid = end.get("id")
        if reachable_ends and eid not in reachable_ends:
            continue
        mapped = set((end.get("outputs") or {}).keys())
        for var in sorted(v for v in outs if v):
            if var not in mapped:
                out.append(fl.finding("warning", "MISSING_OUTPUT_MAPPING",
                                      "out variable %r has no mapping on this reachable End node" % var, node=eid))

    if reference_fields:
        for nid, node in sorted(nodes.items()):
            if not node.get("type", "").startswith(("uipath.connector.", "core.action.http")):
                continue
            detail = ((node.get("inputs") or {}).get("detail") or {})
            for bucket in ("pathParameters", "queryParameters", "bodyParameters"):
                params = detail.get(bucket) or {}
                if not isinstance(params, dict):
                    continue
                for key in sorted(params):
                    value = params[key]
                    if isinstance(value, str) and not value.startswith("=js:") and REFERENCE_HINT.search(key):
                        out.append(fl.finding("info", "REFERENCE_FIELD",
                                              "%s=%r looks like a connection-scoped reference id; re-resolve it "
                                              "against the connection bound to this flow rather than reusing a value "
                                              "from another flow" % (key, value),
                                              node=nid, path="inputs.detail.%s.%s" % (bucket, key)))
    return out

