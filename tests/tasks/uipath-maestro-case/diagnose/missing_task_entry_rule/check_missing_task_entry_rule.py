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

VALID={"wait-for-connector","case-entered","selected-stage-completed","selected-stage-exited",
       "selected-tasks-completed","current-stage-entered","adhoc","required-stages-completed",
       "required-tasks-completed","user-selected-stage","runs-sequentially","sla-status-change"}
p=load()
seen={t.get("displayName") for n in stages(p) for t in tasks(n)}
for want in ("Hold For 1 Hour","Notify Reviewer"):
    if want not in seen: fail(f"task '{want}' was deleted — repair it, don't remove it")
bad=[]
for n in stages(p):
    for t in tasks(n):
        ecs=t.get("entryConditions") or []
        rules=[r for c in ecs for grp in c.get("rules",[]) for r in grp]
        if not ecs or not rules:
            bad.append(f"{label(n)}/{t.get('displayName')}: no entry rule")
        else:
            for r in rules:
                if r.get("rule") not in VALID:
                    bad.append(f"{label(n)}/{t.get('displayName')}: rule '{r.get('rule')}' not in the closed set")
if bad: fail("tasks still lack a usable entry rule (case debug would hang here):\n  - "+"\n  - ".join(bad))
print(f"PASS: all {len(seen)} tasks carry an entry rule from the closed set")
