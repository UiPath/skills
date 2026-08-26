import json,os,re,sys
CP = "LinearThreeStages/LinearThreeStages/caseplan.json"
def fail(m): sys.exit(f"FAIL: {m}")
def load():
    if not os.path.isfile(CP): fail(f"{CP} not found")
    try: return json.load(open(CP))
    except Exception as e: fail(f"{CP} is not valid JSON: {e}")
def stages(p): return [n for n in p.get("nodes",[]) if str(n.get("type","")).endswith("Stage")]
def label(n): return (n.get("data") or {}).get("label")
def tasks(n):
    for lane in ((n.get("data") or {}).get("tasks") or []):
        for t in (lane if isinstance(lane,list) else [lane]): yield t
def all_rules(n):
    for k in ("entryConditions","exitConditions"):
        for c in ((n.get("data") or {}).get(k) or []):
            for grp in c.get("rules",[]):
                for r in grp: yield k,r
def declared(p):
    v=p.get("variables") or {}
    out=set()
    for k in ("inputs","outputs","inputOutputs"):
        for x in (v.get(k) or []):
            if x.get("name"): out.add(x["name"])
            if x.get("var"): out.add(x["var"])
    return out
def refs(obj):
    return set(re.findall(r"\bvars\.([A-Za-z]\w*)", json.dumps(obj)))

p=load()
names={label(n) for n in stages(p)}
for s in ("Intake","Review","Decision"):
    if s not in names: fail(f"stage '{s}' was deleted — repair the defect, don't remove stages")
dec=[n for n in stages(p) if label(n)=="Decision"][0]
gate=[r for _,r in all_rules(dec) if r.get("conditionExpression")]
if not gate: fail("Decision's gate expression was deleted — the fix must keep it gating on the upstream routing decision")
used=refs([r["conditionExpression"] for r in gate])
if not used: fail("Decision's gate no longer references any vars.X")
v=p.get("variables") or {}
allv=[x for k in ("inputs","outputs","inputOutputs") for x in (v.get(k) or [])]
produced={x.get("name") for x in allv if x.get("elementId") and x["elementId"] not in ("root",)}
orphans=sorted(u for u in used if u not in produced)
if orphans:
    fail("Decision's gate still reads "+", ".join(f"vars.{o}" for o in orphans)+
         " which nothing in the case produces. Declaring the variable silences validate but leaves the "
         "gate reading a value no task ever writes — point the gate at the produced variable (or make the "
         "producer write the name the gate reads).")
print(f"PASS: gate reads {sorted(used)}, each produced by a task element; 3 stages intact")
