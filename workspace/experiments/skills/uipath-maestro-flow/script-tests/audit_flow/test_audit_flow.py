import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _helper import check, clean_flow, edge, layout, node, node_vars, read, run, workdir, write

wd = workdir()
clean = write(os.path.join(wd, "clean.flow"), clean_flow())
rc, out = run("audit_flow.py", clean)
check("clean flow exits 0", rc == 0 and "audit: clean" in out, out)
for name in ["topology", "expressions", "jint", "bindings", "runtime-gaps"]:
    check("runs the %s check" % name, name in out, out)

# one dirty flow exercising every chained check at once
f = clean_flow()
f["nodes"] += [
    node("island", "core.action.script", inputs={"script": "console.log(1); return 1;"},
         outputs={"output": {"type": "object", "description": "d", "source": "=result.response", "var": "output"},
                  "error": {"type": "object", "description": "d", "source": "=Error", "var": "error"}}),
    node("route", "core.logic.decision", inputs={"expression": "=js:$vars.buildPayload.output.total > 0"}),
]
f["nodes"] = [n for n in f["nodes"] if n["id"] != "done"] + [
    node("done", "core.control.end", outputs={"total": {"source": "$vars.buildPayload.output.total"}})]
f["edges"].append(edge("start", "output", "route"))
f["edges"].append(edge("route", "true", "done"))
dirty = write(os.path.join(wd, "dirty.flow"), f)
report = os.path.join(wd, "findings.json")
rc, out = run("audit_flow.py", dirty, "--json-out", report)
check("dirty flow exits 1", rc == 1 and "audit: FAIL" in out, out)
data = json.load(open(report))
check("json report holds every check",
      set(data["checks"]) == {"topology", "expressions", "jint", "bindings", "runtime-gaps"}, out)
check("topology finding (dangling node)",
      any(x["code"] == "DANGLING_NODE" for x in data["checks"]["topology"]), out)
check("topology finding (decision branches)",
      any(x["code"] == "DECISION_BRANCHES" for x in data["checks"]["topology"]), out)
check("expression finding (missing =js: on End source)",
      any(x["code"] == "MISSING_JS_PREFIX" for x in data["checks"]["expressions"]), out)
check("expression finding (=js: on a condition)",
      any(x["code"] == "JS_ON_CONDITION" for x in data["checks"]["expressions"]), out)
check("jint finding (console)",
      any(x["code"] == "JINT_UNSUPPORTED" for x in data["checks"]["jint"]), out)
check("jint finding (bare scalar return)",
      any(x["code"] == "SCRIPT_RETURN_SHAPE" for x in data["checks"]["jint"]), out)
check("runtime-gaps finding (missing node variable)",
      any(x["code"] == "MISSING_NODE_VARIABLE" for x in data["checks"]["runtime-gaps"]), out)

rc, out = run("audit_flow.py", dirty, "--only", "jint")
check("--only narrows the run", "jint" in out and "topology" not in out, out)
rc, out = run("audit_flow.py", dirty, "--only", "nope")
check("--only rejects an unknown check", rc == 2 and "unknown check" in out, out)
rc, out = run("audit_flow.py", dirty, "--max-print", "1")
check("--max-print truncates with a pointer", "more (use --json-out" in out, out)

# error-handling shapes
g = clean_flow()
g["nodes"][1]["inputs"]["errorHandlingEnabled"] = True
flagged = write(os.path.join(wd, "flag.flow"), g)
rc, out = run("audit_flow.py", flagged)
check("flag with no error edge", "FLAG_WITHOUT_ERROR_EDGE" in out, out)
h = clean_flow()
h["nodes"][1]["inputs"]["errorHandlingEnabled"] = True
h["edges"].append(edge("buildPayload", "error", "done"))
rejoin = write(os.path.join(wd, "rejoin.flow"), h)
rc, out = run("audit_flow.py", rejoin)
check("error edge rejoining the happy path", "ERROR_REJOINS_HAPPY_PATH" in out, out)

# HITL port, both spellings accepted
i = clean_flow()
i["nodes"].append(node("form", "uipath.human-in-the-loop.quick-form"))
i["edges"] = [edge("start", "output", "form"), edge("buildPayload", "success", "done")]
i["layout"] = layout("start", "buildPayload", "done", "form")
hitl = write(os.path.join(wd, "hitl.flow"), i)
rc, out = run("audit_flow.py", hitl)
check("unwired HITL completion port", "HITL_PORT_UNWIRED" in out, out)
i["edges"].append(edge("form", "outcome-completed", "buildPayload"))
write(hitl, i)
rc, out = run("audit_flow.py", hitl)
check("outcome-completed spelling accepted",
      "HITL_PORT_UNWIRED" not in out and "BAD_SOURCE_PORT" not in out, out)

# resource bindings
RPA_DEF = {"nodeType": "uipath.core.rpa-workflow.abc", "version": "1.0",
           "model": {"bindings": {"resourceKey": "Finance/Automation.Invoice Processor",
                                  "resourceSubType": "Process", "resource": "process"},
                     "context": [{"name": "name", "value": "<bindings.name>"},
                                 {"name": "folderPath", "value": "<bindings.folderPath>"}]}}
j = clean_flow()
j["nodes"].append(node("runRpa", "uipath.core.rpa-workflow.abc"))
j["edges"] = [edge("start", "output", "runRpa"), edge("runRpa", "output", "done")]
j["definitions"].append(RPA_DEF)
j["variables"]["nodes"] += node_vars(("runRpa", "output"))
binds = write(os.path.join(wd, "bind.flow"), j)
rc, out = run("audit_flow.py", binds)
check("missing bindings reported with the debug-time failure",
      rc == 1 and out.count("MISSING_BINDING") == 2 and "Folder does not exist" in out, out)

# ---- fix-plan / --apply ----------------------------------------------------------
k = clean_flow()
k["nodes"][1]["inputs"]["errorHandlingEnabled"] = True                        # flag, no error edge
k["variables"]["nodes"] = [v for v in k["variables"]["nodes"] if v["id"] != "buildPayload.output"]
k["layout"]["nodes"]["buildPayload"]["size"] = {"width": 200, "height": 80}   # wrong size
del k["layout"]["nodes"]["done"]                                              # missing layout
fix = write(os.path.join(wd, "fix.flow"), k)
planfile = os.path.join(wd, "fixes.json")
rc, out = run("audit_flow.py", fix, "--fix-plan", planfile)
ops = json.load(open(planfile))["ops"]
kinds = sorted({o["op"] for o in ops})
check("fix-plan exit 0 when there is something to fix", rc == 0, out)
check("fix-plan emits flow_edit ops", kinds == ["add-node-variable", "set-error-flag", "set-layout"], str(kinds))
check("fix-plan prints the apply command", "flow_edit.py apply --flow" in out, out)
rc, out = run("flow_edit.py", "apply", "--flow", fix, "--plan", planfile)
check("the emitted plan applies cleanly through flow_edit", rc == 0, out)
rc, out = run("audit_flow.py", fix)
check("flow is clean after applying the emitted plan", rc == 0 and "audit: clean" in out, out)

fix2 = write(os.path.join(wd, "fix2.flow"), k)
rc, out = run("audit_flow.py", fix2, "--apply")
check("--apply repairs and re-audits in one call",
      rc == 0 and "repaired" in out and "re-audit after repair" in out and "audit: clean" in out, out)
d = read(fix2)
check("--apply removed the unhandled error flag",
      "errorHandlingEnabled" not in [n for n in d["nodes"] if n["id"] == "buildPayload"][0]["inputs"], out)
check("--apply restored the node variable",
      "buildPayload.output" in {v["id"] for v in d["variables"]["nodes"]}, out)
check("--apply fixed the layout sizes",
      d["layout"]["nodes"]["buildPayload"]["size"] == {"width": 96, "height": 96}
      and d["layout"]["nodes"]["done"]["size"] == {"width": 96, "height": 96}, out)

rc, out = run("audit_flow.py", clean, "--apply")
check("--apply on a clean flow says so", rc == 0 and "no mechanical repair available" in out, out)

# a binding gap whose definition lacks resource/resourceSubType must NOT be auto-applied
thin = dict(RPA_DEF)
thin["model"] = {"bindings": {"resourceKey": "F.R"}, "context": RPA_DEF["model"]["context"]}
m = clean_flow()
m["nodes"].append(node("runRpa", "uipath.core.rpa-workflow.abc"))
m["edges"] = [edge("start", "output", "runRpa"), edge("runRpa", "output", "done")]
m["definitions"].append(thin)
m["variables"]["nodes"] += node_vars(("runRpa", "output"))
partial = write(os.path.join(wd, "partial.flow"), m)
rc, out = run("audit_flow.py", partial, "--apply")
check("incomplete binding definition is surfaced, not guessed",
      "needs a decision" in out and "impl.md" in out, out)
check("incomplete binding still fails the audit", rc == 1 and "MISSING_BINDING" in out, out)

rc, out = run("audit_flow.py", os.path.join(wd, "missing.flow"))
check("missing flow file fails loudly", rc == 2 and "not found" in out, out)
print("audit_flow: all cases passed")
