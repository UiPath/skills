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

EXPECT={"inputs":{"caseRef"},"outputs":{"finalDecision"}}
p=load(); v=p.get("variables") or {}
bad=[]; renamed=[]
for kind in ("inputs","outputs"):
    got={x.get("name") for x in (v.get(kind) or [])}
    missing=EXPECT[kind]-got
    if missing: renamed.append(f"{kind}: {sorted(missing)} no longer present")
    for x in (v.get(kind) or []):
        sid,name,var=x.get("id"),x.get("name"),x.get("var")
        if not sid: bad.append(f"{kind}['{name}'] has no id")
        elif sid==name or (var and sid==var):
            bad.append(f"{kind}['{name}'] id={sid!r} still copies its companion name")
if renamed: fail("variables were renamed or removed instead of re-minting ids:\n  - "+"\n  - ".join(renamed))
if bad: fail("Rule 22 / Check 10 violations remain (CLI validate does not catch these):\n  - "+"\n  - ".join(bad))
n=len((v.get("inputs") or []))+len((v.get("outputs") or []))
print(f"PASS: all {n} formal-arg slot ids are distinct from their companion names; names/vars unchanged")
