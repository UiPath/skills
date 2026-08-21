import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _helper import check, clean_flow, read, run, workdir, write

wd = workdir()
DEF = {"Data": {"Node": {"nodeType": "core.action.transform", "version": "2.1",
                         "outputDefinition": {"properties": {"output": {}, "error": {}}}}}}
END = {"Data": {"Node": {"nodeType": "core.control.end", "version": "1.0", "outputDefinition": {"properties": {}}}}}
DEC = {"Data": {"Node": {"nodeType": "core.logic.decision", "version": "1.0"}}}
SCHED = {"Data": {"Node": {"nodeType": "core.trigger.scheduled", "version": "1.2",
                           "outputDefinition": {"properties": {"output": {}}}}}}
tdef = write(os.path.join(wd, "transform.json"), DEF)
edef = write(os.path.join(wd, "end.json"), END)
ddef = write(os.path.join(wd, "decision.json"), DEC)
sdef = write(os.path.join(wd, "sched.json"), SCHED)


def fresh(name):
    p = os.path.join(wd, name)
    write(p, clean_flow())
    return p


# ---- plan apply: the primary path -------------------------------------------------
f = fresh("plan.flow")
plan = write(os.path.join(wd, "p1.json"), {"ops": [
    {"op": "add-node", "id": "filterRows", "type": "core.action.transform", "definitionFile": tdef,
     "label": "Filter", "inputs": {"collection": "$vars.start.output.items"}},
    {"op": "add-node", "id": "second", "type": "core.action.transform", "definitionFile": tdef},
    {"op": "add-edge", "source": "buildPayload", "sourcePort": "success", "target": "filterRows",
     "targetPort": "input"},
    {"op": "add-edge", "source": "filterRows", "sourcePort": "output", "target": "second", "targetPort": "input"},
    {"op": "add-variable", "id": "count", "direction": "inout", "type": "number", "default": 0},
    {"op": "add-variable-update", "node": "filterRows", "variable": "count", "expression": "=js:$vars.count + 1"},
    {"op": "add-output-mapping", "endNode": "done", "var": "total",
     "source": "=js:$vars.filterRows.output.total"},
]})
rc, out = run("flow_edit.py", "apply", "--flow", f, "--plan", plan)
d = read(f)
check("apply exit 0", rc == 0, out)
check("apply reports each op and the total", out.count("add-node") == 2 and "applied 7 op(s)" in out, out)
check("all nodes added in one call", {"filterRows", "second"} <= {n["id"] for n in d["nodes"]})
check("definition added once for a repeated type",
      sum(1 for x in d["definitions"] if x.get("nodeType") == "core.action.transform") == 1, out)
check("variables.nodes for both nodes",
      {"filterRows.output", "filterRows.error", "second.output"} <= {v["id"] for v in d["variables"]["nodes"]})
check("edges added", len(d["edges"]) == 4, str(d["edges"]))
check("variableUpdates written", d["variables"]["variableUpdates"]["filterRows"][0]["variableId"] == "count")
check("output mapping written",
      [n for n in d["nodes"] if n["id"] == "done"][0]["outputs"]["total"]["source"] == "=js:$vars.filterRows.output.total")
check("layout placeholders written", d["layout"]["nodes"]["second"]["size"] == {"width": 96, "height": 96})

# atomicity: a failing op must leave the file untouched
f2 = fresh("atomic.flow")
before = json.dumps(read(f2), sort_keys=True)
bad = write(os.path.join(wd, "bad.json"), {"ops": [
    {"op": "add-node", "id": "ok1", "type": "core.action.transform", "definitionFile": tdef},
    {"op": "add-edge", "source": "ok1", "sourcePort": "output", "target": "ghost", "targetPort": "input"},
]})
rc, out = run("flow_edit.py", "apply", "--flow", f2, "--plan", bad)
check("failing op exits non-zero", rc == 2, out)
check("failing op names the op index", "op 2" in out, out)
check("nothing written on failure", json.dumps(read(f2), sort_keys=True) == before, "file was mutated")

rc, out = run("flow_edit.py", "apply", "--flow", f2, "--plan", plan, "--dry-run")
check("dry-run writes nothing", rc == 0 and json.dumps(read(f2), sort_keys=True) == before, out)
check("dry-run lists the ops", "would apply" in out, out)

rc, out = run("flow_edit.py", "apply", "--flow", f2, "--plan", os.path.join(wd, "nope.json"))
check("missing plan fails loudly", rc == 2 and "not found" in out, out)
rc, out = run("flow_edit.py", "apply", "--flow", f2,
              "--plan", write(os.path.join(wd, "unknown.json"), {"ops": [{"op": "frobnicate"}]}))
check("unknown op fails loudly and lists the vocabulary", rc == 2 and "unknown op" in out and "add-node" in out, out)
rc, out = run("flow_edit.py", "apply", "--flow", f2,
              "--plan", write(os.path.join(wd, "empty.json"), {"ops": []}))
check("empty plan fails loudly", rc == 2, out)

# ---- refusals carried over from the skill's rules --------------------------------
f3 = fresh("refuse.flow")
cli = write(os.path.join(wd, "cli.json"), {"ops": [
    {"op": "add-node", "id": "sendSlack", "type": "uipath.connector.uipath-salesforce-slack.send-message",
     "typeVersion": "1.0"}]})
rc, out = run("flow_edit.py", "apply", "--flow", f3, "--plan", cli)
check("CLI-owned node refused with exit 3", rc == 3 and "node add" in out, out)
badid = write(os.path.join(wd, "badid.json"), {"ops": [
    {"op": "add-node", "id": "1bad", "type": "core.action.transform", "definitionFile": tdef}]})
rc, out = run("flow_edit.py", "apply", "--flow", f3, "--plan", badid)
check("id not starting with a letter refused", rc == 2 and "must start with a letter" in out, out)
ver = write(os.path.join(wd, "ver.json"), {"ops": [
    {"op": "add-node", "id": "x", "type": "core.action.transform", "typeVersion": "9.9", "definitionFile": tdef}]})
rc, out = run("flow_edit.py", "apply", "--flow", f3, "--plan", ver)
check("typeVersion mismatch refused", rc == 2 and "string-match" in out, out)
noport = write(os.path.join(wd, "noport.json"), {"ops": [
    {"op": "add-edge", "source": "start", "sourcePort": "output", "target": "buildPayload"}]})
rc, out = run("flow_edit.py", "apply", "--flow", f3, "--plan", noport)
check("missing targetPort refused", rc == 2 and "targetPort is required" in out, out)
errflag = write(os.path.join(wd, "err.json"), {"ops": [
    {"op": "add-node", "id": "handler", "type": "core.action.transform", "definitionFile": tdef},
    {"op": "add-edge", "source": "buildPayload", "sourcePort": "error", "target": "handler", "targetPort": "input"}]})
rc, out = run("flow_edit.py", "apply", "--flow", f3, "--plan", errflag)
check("error edge sets errorHandlingEnabled",
      [n for n in read(f3)["nodes"] if n["id"] == "buildPayload"][0]["inputs"]["errorHandlingEnabled"] is True, out)
upd = write(os.path.join(wd, "upd.json"), {"ops": [
    {"op": "add-variable-update", "node": "buildPayload", "variable": "total", "expression": "=js:1"}]})
rc, out = run("flow_edit.py", "apply", "--flow", f3, "--plan", upd)
check("variableUpdate on a non-inout variable refused", rc == 2 and "inout" in out, out)

# ---- composites as plan ops ------------------------------------------------------
f4 = fresh("comp.flow")
comp = write(os.path.join(wd, "comp.json"), {"ops": [
    {"op": "add-node", "id": "hi", "type": "core.action.transform", "definitionFile": tdef},
    {"op": "add-node", "id": "lo", "type": "core.action.transform", "definitionFile": tdef},
    {"op": "insert-decision", "upstream": "buildPayload", "id": "route", "definitionFile": ddef,
     "expression": "$vars.buildPayload.output.total > 0", "trueTarget": "hi", "falseTarget": "lo"},
    {"op": "add-edge", "source": "hi", "sourcePort": "output", "target": "done", "targetPort": "input"},
    {"op": "add-edge", "source": "lo", "sourcePort": "output", "target": "done", "targetPort": "input"},
]})
rc, out = run("flow_edit.py", "apply", "--flow", f4, "--plan", comp)
d = read(f4)
ports = sorted(e["sourcePort"] for e in d["edges"] if e["sourceNodeId"] == "route")
check("insert-decision wired true/false in the same call", rc == 0 and ports == ["false", "true"], out)
check("insert-decision removed the replaced edge",
      not any(e["sourceNodeId"] == "buildPayload" and e["targetNodeId"] == "done" for e in d["edges"]))
check("decision expression is not js-prefixed",
      [n for n in d["nodes"] if n["id"] == "route"][0]["inputs"]["expression"].startswith("$vars"))

f5 = fresh("ib.flow")
rc, out = run("flow_edit.py", "apply", "--flow", f5, "--plan", write(os.path.join(wd, "ib.json"), {"ops": [
    {"op": "insert-between", "upstream": "start", "downstream": "buildPayload", "id": "pause",
     "type": "core.action.transform", "definitionFile": tdef}]}))
d = read(f5)
check("insert-between splices in one op",
      rc == 0 and any(e["sourceNodeId"] == "start" and e["targetNodeId"] == "pause" for e in d["edges"])
      and any(e["sourceNodeId"] == "pause" and e["targetNodeId"] == "buildPayload" for e in d["edges"]), out)
rc, out = run("flow_edit.py", "apply", "--flow", f5, "--plan", write(os.path.join(wd, "rr.json"), {"ops": [
    {"op": "remove-reconnect", "id": "pause"}]}))
check("remove-reconnect bridges the gap",
      rc == 0 and any(e["sourceNodeId"] == "start" and e["targetNodeId"] == "buildPayload" for e in read(f5)["edges"]), out)
rc, out = run("flow_edit.py", "apply", "--flow", f5, "--plan", write(os.path.join(wd, "rt.json"), {"ops": [
    {"op": "replace-trigger-scheduled", "node": "start", "definitionFile": sdef, "timerPreset": "R/PT1H"}]}))
n = [x for x in read(f5)["nodes"] if x["id"] == "start"][0]
check("replace-trigger-scheduled swaps type and keeps entryPointId",
      n["type"] == "core.trigger.scheduled" and n["inputs"]["timerPreset"] == "R/PT1H"
      and "entryPointId" in n["inputs"], str(n))

# ---- delete cascade --------------------------------------------------------------
f6 = fresh("del.flow")
run("flow_edit.py", "apply", "--flow", f6, "--plan", write(os.path.join(wd, "d1.json"), {"ops": [
    {"op": "add-node", "id": "tmp", "type": "core.action.transform", "definitionFile": tdef},
    {"op": "add-edge", "source": "buildPayload", "sourcePort": "success", "target": "tmp", "targetPort": "input"}]}))
rc, out = run("flow_edit.py", "apply", "--flow", f6, "--plan", write(os.path.join(wd, "d2.json"), {"ops": [
    {"op": "delete-node", "id": "tmp"}]}))
d = read(f6)
check("delete-node cascades edges, variables, layout, definition",
      rc == 0 and not any(n["id"] == "tmp" for n in d["nodes"])
      and not any("tmp" in (e["sourceNodeId"], e["targetNodeId"]) for e in d["edges"])
      and not any(v["binding"]["nodeId"] == "tmp" for v in d["variables"]["nodes"])
      and "tmp" not in d["layout"]["nodes"]
      and not any(x.get("nodeType") == "core.action.transform" for x in d["definitions"]), out)

# ---- single-op fallbacks still work ----------------------------------------------
f7 = fresh("fallback.flow")
rc, out = run("flow_edit.py", "add-node", "--flow", f7, "--id", "one",
              "--type", "core.action.transform", "--definition-file", tdef)
check("add-node fallback", rc == 0 and any(n["id"] == "one" for n in read(f7)["nodes"]), out)
rc, out = run("flow_edit.py", "add-edge", "--flow", f7, "--source", "buildPayload",
              "--source-port", "success", "--target", "one", "--target-port", "input")
check("add-edge fallback derives the id pattern",
      any(e["id"] == "edge_buildPayload_success_one_input" for e in read(f7)["edges"]), out)
rc, out = run("flow_edit.py", "set-input", "--flow", f7, "--node", "one", "--key", "a.b", "--value", "v")
check("set-input fallback writes a nested key",
      [n for n in read(f7)["nodes"] if n["id"] == "one"][0]["inputs"]["a"]["b"] == "v", out)

# ---- plan-schema is discoverable without reading source --------------------------
rc, out = run("flow_edit.py", "plan-schema")
check("plan-schema lists every op", rc == 0 and all(k in out for k in
      ["add-node", "add-edge", "insert-decision", "agent-inputs", "add-bindings", "set-error-flag"]), out)

# ---- agent-inputs ----------------------------------------------------------------
rc, out = run("flow_edit.py", "agent-inputs", "emit", "--source", "$vars.start.output.invoiceNumber")
payload = json.loads(out)
check("agent-inputs emit flattens per the rule",
      payload["flowNode"]["inputs"]["agentInputVariables"][0]["id"] == "start__output__invoiceNumber", out)
check("agent-inputs emit uses binding, never value",
      "binding" in payload["flowNode"]["inputs"]["agentInputVariables"][0]
      and "value" not in payload["flowNode"]["inputs"]["agentInputVariables"][0], out)
check("agent-inputs emit writes no contentTokens", "contentTokens" not in out, out)

f8 = fresh("agent.flow")
d = read(f8)
d["nodes"].append({"id": "triage", "type": "uipath.agent.autonomous", "typeVersion": "1.0",
                   "display": {"label": "T"}, "inputs": {"source": "u1"}})
d["edges"].append({"id": "e_bp_triage", "sourceNodeId": "buildPayload", "sourcePort": "success",
                   "targetNodeId": "triage", "targetPort": "input"})
d["variables"]["globals"].append({"id": "invoiceNumber", "direction": "in", "type": "string",
                                  "triggerNodeId": "start"})
write(f8, d)
rc, out = run("flow_edit.py", "apply", "--flow", f8, "--plan", write(os.path.join(wd, "ai.json"), {"ops": [
    {"op": "agent-inputs", "node": "triage", "sources": ["$vars.start.output.invoiceNumber:string"]}]}))
check("agent-inputs op writes agentInputVariables",
      rc == 0 and [n for n in read(f8)["nodes"] if n["id"] == "triage"][0]["inputs"]["agentInputVariables"][0]["binding"]
      == "=$vars.start.output.invoiceNumber", out)
aj = write(os.path.join(wd, "agent.json"), {
    "inputSchema": {"type": "object", "properties": {"start__output__invoiceNumber": {"type": "string"}}},
    "messages": [{"role": "user", "content": "Invoice: {{input.start__output__invoiceNumber}}"}]})
rc, out = run("flow_edit.py", "agent-inputs", "check", "--flow", f8, "--agent-json", aj)
check("agent-inputs check passes on an aligned triple", rc == 0 and "0 error(s)" in out, out)
bad_aj = write(os.path.join(wd, "bad_agent.json"), {
    "inputSchema": {"type": "object", "properties": {"other": {"type": "object"}}},
    "messages": [{"role": "user", "content": "X {{ $vars.start.output.invoiceNumber }}"}]})
rc, out = run("flow_edit.py", "agent-inputs", "check", "--flow", f8, "--agent-json", bad_aj)
check("agent-inputs check flags misalignment and raw $vars tokens",
      rc == 1 and "MISSING_IN_SCHEMA" in out and "RAW_VARS_TOKEN" in out, out)
print("flow_edit: all cases passed")
