"""The five audit modules have no CLI; their collect() functions are tested directly."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _helper import check, clean_flow, edge, layout, node, node_vars, workdir, write

from _flow import bindings, expressions, jint, lib, runtime_gaps, topology


def codes(findings):
    return {f["code"] for f in findings}


def sev(findings, s):
    return [f for f in findings if f["severity"] == s]


wd = workdir()
clean = clean_flow()
for name, mod in (("topology", topology), ("expressions", expressions), ("jint", jint), ("runtime-gaps", runtime_gaps)):
    check("%s: clean flow has no error" % name, not sev(mod.collect(clean) if name != "runtime-gaps"
                                                        else mod.collect(clean, False), "error"))
check("bindings: clean flow has no error", not sev(bindings.collect(clean)[0], "error"))
check("no module exposes a CLI", all(not hasattr(m, "main") for m in (topology, expressions, jint, bindings, runtime_gaps)))

# topology: port table + wiring rules
f = clean_flow()
f["edges"] = [
    {"id": "e1", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "buildPayload"},
    {"id": "e2", "sourceNodeId": "buildPayload", "sourceHandle": "success", "targetNodeId": "done", "targetPort": "input"},
    edge("buildPayload", "notAPort", "done"),
    edge("buildPayload", "success", "start"),
    edge("done", "output", "buildPayload"),
    edge("buildPayload", "error", "done"),
]
f["nodes"] += [node("island", "core.action.script"), node("route", "core.logic.decision")]
f["edges"] += [edge("start", "output", "route"), edge("route", "true", "done")]
got = codes(topology.collect(f))
for c in ("MISSING_TARGET_PORT", "SOURCE_HANDLE", "BAD_SOURCE_PORT", "TRIGGER_AS_TARGET", "TERMINAL_AS_SOURCE",
          "DANGLING_NODE", "DECISION_BRANCHES", "ERROR_EDGE_WITHOUT_FLAG", "ILLEGAL_CYCLE"):
    check("topology reports %s" % c, c in got, str(sorted(got)))
g = clean_flow()
g["nodes"].append(node("loopIt", "core.logic.loop"))
g["edges"] = [edge("start", "output", "loopIt"), edge("loopIt", "output", "buildPayload"),
              edge("buildPayload", "success", "loopIt", "loopBack"), edge("loopIt", "success", "done")]
check("topology: loopBack cycle is legal", "ILLEGAL_CYCLE" not in codes(topology.collect(g)))
h = clean_flow()
h["nodes"].append(node("form", "uipath.human-in-the-loop.quick-form"))
h["edges"] = [edge("start", "output", "form"), edge("form", "outcome-completed", "buildPayload"),
              edge("buildPayload", "success", "done")]
check("topology: both HITL port spellings accepted", "BAD_SOURCE_PORT" not in codes(topology.collect(h)))

# expressions: the per-field matrix
f = clean_flow()
f["nodes"] += [
    node("createRec", "uipath.connector.uipath-uipath-dataservice.create-entity-record", inputs={
        "detail": {"queryParameters": {"recordId": "$vars.buildPayload.output.id",
                                       "ok": "=js:$vars.buildPayload.output.id", "static": "HDFC Bank"},
                   "bodyParameters": {"Note": "{$vars.buildPayload.output.total}",
                                      "Bad": "nodes.buildPayload.output.total"}}}),
    node("route", "core.logic.decision", inputs={"expression": "=js:$vars.buildPayload.output.total > 0"}),
    node("pick", "core.logic.switch", inputs={"cases": [{"id": "c1", "expression": "$vars.x === 1"}]}),
    node("filterRows", "core.action.transform.filter", inputs={"collection": "$vars.buildPayload.output.items"}),
    node("loopIt", "core.logic.loop", inputs={"collection": "$vars.buildPayload.output.items"}),
]
f["variables"]["variableUpdates"] = {"buildPayload": [{"variableId": "c", "expression": "$vars.c + 1"}]}
out = expressions.collect(f)
got = codes(out)
for c in ("MISSING_JS_PREFIX", "INVENTED_NODES_SYNTAX", "BRACE_INTERPOLATION", "JS_ON_CONDITION"):
    check("expressions reports %s" % c, c in got, str(sorted(got)))
paths = {f_["path"] for f_ in out if f_.get("path")}
check("expressions: connector queryParameter path pinpointed",
      "inputs.detail.queryParameters.recordId" in paths, str(sorted(paths)))
check("expressions: prefixed value not flagged", "inputs.detail.queryParameters.ok" not in paths)
check("expressions: static value not flagged", "inputs.detail.queryParameters.static" not in paths)
check("expressions: switch case condition accepted without prefix",
      not any(p.startswith("inputs.cases") for p in paths))
check("expressions: transform collection path is at most a warning",
      not any(f_["severity"] == "error" and f_.get("node") == "filterRows" for f_ in out))
check("expressions: loop collection requires the prefix",
      any(f_["code"] == "MISSING_JS_PREFIX" and f_.get("node") == "loopIt" for f_ in out))
check("expressions: variableUpdates expression checked",
      any("variableUpdates" in (f_.get("path") or "") for f_ in out))

# jint: unsupported constructs + script rules
f = clean_flow()
f["nodes"] += [
    node("logs", "core.action.script", inputs={"script": "console.log('x');\nreturn { a: 1 };"}),
    node("waits", "core.action.script", inputs={"script": "const r = await fetch('http://x');\nreturn { r };"}),
    node("wrapped", "core.action.script", inputs={"script": "function main() { return { a: 1 }; }"}),
    node("noReturn", "core.action.script", inputs={"script": "const a = 1;"}),
    node("scalar", "core.action.script", inputs={"script": "return 42;"}),
    node("agg", "core.action.script", inputs={"script": "const aggregate = 1;\nreturn { aggregate };"}),
    node("dated", "core.action.script", inputs={"script": "const d = new Date();\nreturn { d };"}),
    node("exprNode", "core.logic.delay", inputs={"duration": "=js:new Promise(r => r(1))"}),
    node("noBody", "core.action.script", inputs={}),
]
out = jint.collect(f)
got = codes(out)
for c in ("JINT_UNSUPPORTED", "SCRIPT_MAIN_WRAPPER", "SCRIPT_NO_RETURN", "SCRIPT_RETURN_SHAPE",
          "SCRIPT_RESERVED_AGGREGATE", "SCRIPT_MISSING_BODY"):
    check("jint reports %s" % c, c in got, str(sorted(got)))
msgs = " ".join(f_["message"] for f_ in out)
for label in ("console", "await", "fetch", "Promise", "Date constructor"):
    check("jint names %s" % label, label in msgs, msgs[:200])
check("jint scans =js: expressions too", any(f_.get("node") == "exprNode" for f_ in out))

# bindings: pair audit + emit shape
RPA_DEF = {"nodeType": "uipath.core.rpa-workflow.abc", "version": "1.0",
           "model": {"bindings": {"resourceKey": "Finance/Automation.Invoice Processor",
                                  "resourceSubType": "Process", "resource": "process"},
                     "context": [{"name": "name", "value": "<bindings.name>"},
                                 {"name": "folderPath", "value": "<bindings.folderPath>"}]}}
f = clean_flow()
f["nodes"].append(node("runRpa", "uipath.core.rpa-workflow.abc"))
f["edges"] = [edge("start", "output", "runRpa"), edge("runRpa", "output", "done")]
f["definitions"].append(RPA_DEF)
f["variables"]["nodes"] += node_vars(("runRpa", "output"))
found, missing = bindings.collect(f)
by_name = {m["name"]: m for m in missing}
check("bindings: two entries missing", len(missing) == 2 and set(by_name) == {"name", "folderPath"}, str(missing))
check("bindings: resourceKey split into defaults",
      by_name["name"]["default"] == "Invoice Processor" and by_name["folderPath"]["default"] == "Finance/Automation")
check("bindings: resourceSubType and resource copied from the definition",
      by_name["name"]["resourceSubType"] == "Process" and by_name["name"]["resource"] == "process")
check("bindings: ids start with a letter", all(m["id"][0].isalpha() for m in missing))
check("bindings: the debug-time failure is quoted",
      any("Folder does not exist" in f_["message"] for f_ in found))
f["bindings"] = missing
check("bindings: clean once the pair exists", not sev(bindings.collect(f)[0], "error"))
f["bindings"] = missing + [dict(missing[0], id="dupe")]
check("bindings: duplicate pair warned", "DUPLICATE_BINDING" in codes(bindings.collect(f)[0]))
f["definitions"] = [d for d in f["definitions"] if d.get("nodeType") != "uipath.core.rpa-workflow.abc"]
check("bindings: missing definition reported", "NO_DEFINITION" in codes(bindings.collect(f)[0]))

# runtime gaps
f = clean_flow()
f["nodes"][1]["inputs"]["errorHandlingEnabled"] = True
check("runtime-gaps: flag with no error edge",
      "FLAG_WITHOUT_ERROR_EDGE" in codes(runtime_gaps.collect(f, False)))
g = clean_flow()
g["nodes"][1]["inputs"]["errorHandlingEnabled"] = True
g["nodes"].append(node("logError", "core.action.script", inputs={"script": "return { e: 1 };"}))
g["edges"] += [edge("buildPayload", "error", "logError"), edge("logError", "success", "done")]
g["layout"] = layout("start", "buildPayload", "done", "logError")
g["variables"]["nodes"] += node_vars(("logError", "output"))
check("runtime-gaps: error path sharing the success terminal",
      "ERROR_SHARES_SUCCESS_TERMINAL" in codes(runtime_gaps.collect(g, False)))
h = clean_flow()
h["nodes"].append(node("agent1", "uipath.agent.autonomous", inputs={"source": "u1"},
                       outputs={"output": {"type": "object", "description": "d",
                                           "source": "=result.response", "var": "output"}}))
h["edges"] = [edge("start", "output", "agent1"), edge("agent1", "success", "done")]
h["layout"] = layout("start", "buildPayload", "done", "agent1")
h["variables"]["nodes"] += node_vars(("agent1", "output"))
out = runtime_gaps.collect(h, False)
check("runtime-gaps: inline-agent layout size mismatch (288x96)",
      any(f_["code"] == "LAYOUT_SIZE_MISMATCH" and "288" in f_["message"] for f_ in out), str(out))
i = clean_flow()
i["variables"]["nodes"] = [v for v in i["variables"]["nodes"] if v["id"] != "buildPayload.output"]
check("runtime-gaps: missing node variable",
      "MISSING_NODE_VARIABLE" in codes(runtime_gaps.collect(i, False)))
j = clean_flow()
j["nodes"].append(node("route", "core.logic.decision", inputs={"expression": "$vars.x > 1"}))
j["edges"] += [edge("buildPayload", "success", "route"), edge("route", "true", "done"),
               edge("route", "false", "done")]
j["layout"] = layout("start", "buildPayload", "done", "route")
check("runtime-gaps: a control-flow node that declares no output is not asked for one",
      "MISSING_NODE_VARIABLE" not in codes(runtime_gaps.collect(j, False)))
k = clean_flow()
k["nodes"][2]["outputs"] = {}
check("runtime-gaps: out variable unmapped on a reachable End node",
      "MISSING_OUTPUT_MAPPING" in codes(runtime_gaps.collect(k, False)))
m = clean_flow()
m["nodes"].append(node("1bad", "core.action.script"))
m["edges"].append({"id": "12-uuid", "sourceNodeId": "start", "sourcePort": "output",
                   "targetNodeId": "1bad", "targetPort": "input"})
got = codes(runtime_gaps.collect(m, False))
check("runtime-gaps: ids that do not start with a letter",
      {"BAD_NODE_ID", "BAD_EDGE_ID"} <= got, str(sorted(got)))
p = clean_flow()
p["nodes"].append(node("post", "uipath.connector.uipath-salesforce-slack.post-message",
                       inputs={"detail": {"bodyParameters": {"channelId": "C123456", "text": "hi"}}}))
p["edges"] = [edge("start", "output", "post"), edge("post", "output", "done")]
p["layout"] = layout("start", "buildPayload", "done", "post")
p["variables"]["nodes"] += node_vars(("post", "output"))
check("runtime-gaps: reference fields silent by default",
      "REFERENCE_FIELD" not in codes(runtime_gaps.collect(p, False)))
check("runtime-gaps: reference fields listed on request",
      "REFERENCE_FIELD" in codes(runtime_gaps.collect(p, True)))

# lib: loader contract
bad = write(os.path.join(wd, "bad.json"), "{not json")
try:
    lib.load(bad)
    check("lib: invalid JSON fails loudly", False, "no SystemExit")
except SystemExit as exc:
    check("lib: invalid JSON fails loudly", exc.code == 2, str(exc))
print("_flow modules: all cases passed")
