#!/usr/bin/env python3
"""Per-task trace features used for attribution."""
import json, re, collections
BUNDLED = {"flow_edit","flow_compose","audit_flow","check_topology","audit_expressions","lint_jint",
           "check_bindings","check_runtime_gaps","node_ownership","validate_mermaid",
           "encode_parameter_values","wire_agent_inputs","diagnose_run","flow_lib"}
REF = re.compile(r"uipath-maestro-flow/(references|SKILL\.md)")
SCRIPTSRC = re.compile(r"uipath-maestro-flow/scripts/[a-z_]+\.py")
HELP = re.compile(r"scripts/[a-z_]+\.py\s+(?:[a-z-]+\s+)?--help")
UIP = re.compile(r"\buip\s+([a-z]+(?:\s+[a-z]+){0,2})")
PYINLINE = re.compile(r"python3?\s+(-c|-\s*<<|- )")

def feats(side):
    f = collections.Counter()
    ref_tokens = 0
    src_tokens = 0
    uip_verbs = collections.Counter()
    for c in side["trace"]:
        tool = c["tool"]; det = c["detail"] or ""; rt = c["result_tokens"]
        f["calls"] += 1
        f["tool_" + tool] += 1
        if REF.search(det):
            f["ref_touch"] += 1; ref_tokens += rt
        if SCRIPTSRC.search(det) and not HELP.search(det) and "flow_edit.py add" not in det:
            if tool == "Read" or re.search(r"\b(cat|sed|head|less|grep)\b", det):
                f["script_source_read"] += 1; src_tokens += rt
        if HELP.search(det):
            f["script_help"] += 1
        if tool == "Bash":
            for v in UIP.findall(det):
                uip_verbs[" ".join(v.split()[:3])] += 1
            if PYINLINE.search(det):
                f["inline_python"] += 1
        if tool in ("TaskCreate", "TaskUpdate", "TodoWrite"):
            f["todo"] += 1
        if tool in ("AskUserQuestion", "SendMessage"):
            f["ask"] += 1
    f["validate"] = sum(v for k, v in uip_verbs.items() if k.startswith("maestro flow validate"))
    f["format"] = sum(v for k, v in uip_verbs.items() if k.startswith("maestro flow format"))
    f["registry"] = sum(v for k, v in uip_verbs.items() if k.startswith("maestro flow registry"))
    f["node_cli"] = sum(v for k, v in uip_verbs.items() if k.startswith(("maestro flow node", "maestro flow edge")))
    f["ref_tokens"] = ref_tokens
    f["src_tokens"] = src_tokens
    return dict(f)

D = json.load(open("rows.json"))
out = []
for r in D["rows"]:
    row = {k: r[k] for k in r if not k.endswith(("opt", "base"))}
    row["fb"] = feats(r["base"]); row["fo"] = feats(r["opt"])
    for side in ("base", "opt"):
        row[side] = {k: v for k, v in r[side].items() if k != "trace"}
    out.append(row)
json.dump(out, open("features.json", "w"), indent=1)
tot = collections.Counter()
for r in out:
    for k in ("ref_touch", "script_source_read", "script_help", "inline_python", "todo", "ask", "validate", "format", "registry", "node_cli"):
        tot["B_" + k] += r["fb"].get(k, 0); tot["O_" + k] += r["fo"].get(k, 0)
    tot["B_ref_tokens"] += r["fb"].get("ref_tokens", 0); tot["O_ref_tokens"] += r["fo"].get("ref_tokens", 0)
    tot["B_src_tokens"] += r["fb"].get("src_tokens", 0); tot["O_src_tokens"] += r["fo"].get("src_tokens", 0)
for k in sorted(tot):
    print("%-20s %d" % (k, tot[k]))
print("\ntasks where OPT read script source:", sum(1 for r in out if r["fo"].get("script_source_read")))
print("tasks where OPT called --help on a script:", sum(1 for r in out if r["fo"].get("script_help")))
print("Δ$ on those:", round(sum(r["d_cost"] for r in out if r["fo"].get("script_source_read") or r["fo"].get("script_help")), 2))
