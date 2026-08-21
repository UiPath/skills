"""Check `.flow` wiring against the Standard Port Reference and the wiring rules.

Reports port names that do not exist for a node type, triggers used as targets, End/terminate
used as sources, missing incoming/outgoing edges, unbalanced decision/switch branches,
dangling nodes, illegal cycles, and error edges without inputs.errorHandlingEnabled.
"""

from . import lib as fl

EXACT = {
    "core.trigger.manual": ([], ["output"]),
    "core.trigger.scheduled": ([], ["output"]),
    "core.action.script": (["input"], ["success", "error"]),
    "core.action.http.v2": (["input"], ["default", "error"]),
    "core.action.http": (["input"], ["default", "error"]),
    "core.action.transform": (["input"], ["output", "error"]),
    "uipath.pattern.batch-transform": (["input"], ["output", "error"]),
    "uipath.pattern.deep-rag": (["input"], ["output", "error"]),
    "core.logic.delay": (["input"], ["output"]),
    "core.logic.decision": (["input"], ["true", "false"]),
    "core.logic.switch": (["input"], ["default"]),
    "core.logic.loop": (["input", "loopBack"], ["success", "output", "error"]),
    "core.logic.merge": (["input"], ["output"]),
    "core.control.end": (["input"], []),
    "core.logic.terminate": (["input"], []),
    "core.subflow": (["input"], ["output", "error"]),
    "core.logic.mock": (["input"], ["output"]),
    "uipath.agent.autonomous": (["input"], ["success", "error", "tool", "context", "escalation"]),
    "core.action.queue.create": (["input"], ["success"]),
    "core.action.queue.create-and-wait": (["input"], ["success"]),
    # hitl/impl.md names this port outcome-completed; planning-arch.md and failure-modes.md
    # name it completed. Both spellings are accepted and the mismatch is reported.
    "uipath.human-in-the-loop.quick-form": (["input"], ["completed", "outcome-completed"]),
}
PREFIX = [
    ("uipath.connector.trigger.", ([], ["output"])),
    ("uipath.connector.event.", (["input"], ["output", "error"])),
    ("uipath.connector.", (["input"], ["output", "error"])),
    ("core.action.transform.", (["input"], ["output", "error"])),
    ("uipath.core.agent.", (["input"], ["output", "error"])),
    ("uipath.core.rpa-workflow.", (["input"], ["output", "error"])),
    ("uipath.core.human-task.", (["input"], ["output", "error"])),
    ("uipath.core.flow.", (["input"], ["output", "error"])),
    ("uipath.core.agentic-process.", (["input"], ["output", "error"])),
    ("uipath.core.api-workflow.", (["input"], ["output", "error"])),
    ("uipath.ixp.", (["input"], ["success", "error"])),
]
DYNAMIC_SOURCE = {"core.action.http.v2": "branch-", "core.action.http": "branch-", "core.logic.switch": "case-"}


def ports(ntype):
    if ntype in EXACT:
        return EXACT[ntype]
    for prefix, spec in PREFIX:
        if ntype.startswith(prefix):
            return spec
    return None


def collect(flow):
    out = []
    nodes = fl.node_map(flow)
    seen_ids = set()
    for n in flow["nodes"]:
        nid = n.get("id")
        if nid in seen_ids:
            out.append(fl.finding("error", "DUPLICATE_NODE_ID", "node id is used more than once", node=nid))
        seen_ids.add(nid)
    seen_edges = set()
    for e in flow["edges"]:
        eid = e.get("id", "<no id>")
        if eid in seen_edges:
            out.append(fl.finding("error", "DUPLICATE_EDGE_ID", "edge id is used more than once", edge=eid))
        seen_edges.add(eid)
        if "sourceHandle" in e:
            out.append(fl.finding("error", "SOURCE_HANDLE", "edge uses sourceHandle; the field is sourcePort", edge=eid))
        src, tgt = e.get("sourceNodeId"), e.get("targetNodeId")
        sp, tp = e.get("sourcePort"), e.get("targetPort")
        if not sp:
            out.append(fl.finding("error", "MISSING_SOURCE_PORT", "edge has no sourcePort", edge=eid))
        if not tp:
            out.append(fl.finding("error", "MISSING_TARGET_PORT", "edge has no targetPort; validate rejects this", edge=eid))
        for role, nid in (("sourceNodeId", src), ("targetNodeId", tgt)):
            if nid not in nodes:
                out.append(fl.finding("error", "UNKNOWN_NODE_REF", "%s %r does not exist" % (role, nid), edge=eid))
        if src in nodes and sp:
            stype = nodes[src].get("type", "")
            spec = ports(stype)
            if spec is None:
                out.append(fl.finding("info", "UNKNOWN_NODE_TYPE",
                                      "%s is not in the port reference; ports not checked" % stype, node=src))
            else:
                allowed = set(spec[1])
                if not fl.is_trigger(stype) and not fl.is_terminal(stype):
                    allowed.add("error")
                dyn = DYNAMIC_SOURCE.get(stype)
                ok = sp in allowed or (dyn and sp.startswith(dyn))
                if not ok:
                    out.append(fl.finding("error", "BAD_SOURCE_PORT",
                                          "%s has no source port %r (allowed: %s%s)"
                                          % (stype, sp, ", ".join(sorted(allowed)),
                                             ", %s{id}" % dyn if dyn else ""), edge=eid, node=src))
                if sp == "error" and (nodes[src].get("inputs") or {}).get("errorHandlingEnabled") is not True:
                    out.append(fl.finding("error", "ERROR_EDGE_WITHOUT_FLAG",
                                          "error edge leaves this node but inputs.errorHandlingEnabled is not true",
                                          node=src, edge=eid))
            if fl.is_terminal(stype):
                out.append(fl.finding("error", "TERMINAL_AS_SOURCE",
                                      "%s has no output port; it can only be an edge target" % stype, node=src, edge=eid))
        if tgt in nodes and tp:
            ttype = nodes[tgt].get("type", "")
            spec = ports(ttype)
            if spec is not None:
                if tp not in set(spec[0]):
                    out.append(fl.finding("error", "BAD_TARGET_PORT",
                                          "%s has no target port %r (allowed: %s)"
                                          % (ttype, tp, ", ".join(sorted(spec[0])) or "none"), edge=eid, node=tgt))
            if fl.is_trigger(ttype):
                out.append(fl.finding("error", "TRIGGER_AS_TARGET",
                                      "%s has no input port; triggers are always edge sources" % ttype, node=tgt, edge=eid))

    for nid, n in sorted(nodes.items()):
        ntype = n.get("type", "")
        ins, outs = fl.in_edges(flow, nid), fl.out_edges(flow, nid)
        if not ins and not outs:
            out.append(fl.finding("error", "DANGLING_NODE", "node has no incoming and no outgoing edge", node=nid))
            continue
        if not fl.is_trigger(ntype) and not ins:
            out.append(fl.finding("error", "NO_INCOMING", "non-trigger node has no incoming edge", node=nid))
        if not fl.is_terminal(ntype) and not outs:
            out.append(fl.finding("error", "NO_OUTGOING", "non-terminal node has no outgoing edge", node=nid))
        if ntype == "core.logic.decision":
            for port in ("true", "false"):
                cnt = len(fl.out_edges(flow, nid, port))
                if cnt != 1:
                    out.append(fl.finding("error", "DECISION_BRANCHES",
                                          "decision needs exactly one %r edge, found %d" % (port, cnt), node=nid))
        if ntype == "core.logic.switch":
            cases = [e for e in outs if (e.get("sourcePort") or "").startswith("case-")]
            if not cases:
                out.append(fl.finding("error", "SWITCH_CASES", "switch has no case-{id} edge", node=nid))

    out += cycles(flow)
    return out


def cycles(flow):
    adj = {}
    for e in flow["edges"]:
        if e.get("targetPort") == "loopBack":
            continue
        adj.setdefault(e.get("sourceNodeId"), []).append((e.get("targetNodeId"), e.get("id")))
    found, state = [], {}

    def walk(nid, stack):
        state[nid] = 1
        for nxt, eid in sorted(adj.get(nid, []), key=lambda x: (str(x[0]), str(x[1]))):
            if state.get(nxt) == 1:
                found.append(fl.finding("error", "ILLEGAL_CYCLE",
                                        "cycle %s -> %s; back edges must arrive on a loop node's loopBack port"
                                        % (" -> ".join(stack + [str(nid)]), nxt), edge=eid))
            elif state.get(nxt) is None:
                walk(nxt, stack + [str(nid)])
        state[nid] = 2

    for nid in sorted(fl.node_map(flow)):
        if state.get(nid) is None:
            walk(nid, [])
    return found

