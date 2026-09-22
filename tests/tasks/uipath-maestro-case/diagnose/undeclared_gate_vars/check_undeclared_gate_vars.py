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

MUST={"approvalTier","riskBand","escalationPath"}
p=load()
exprs=[]
for n in stages(p):
    for _,r in all_rules(n):
        if r.get("conditionExpression"): exprs.append((label(n),r["conditionExpression"]))
used=refs([e for _,e in exprs])
gone=sorted(MUST-used)
if gone:
    fail("gate expression(s) referencing "+", ".join(gone)+" were deleted or blanked. The fix is to DECLARE "
         "the variables, not to remove the gates.")
dec=declared(p)
undeclared=sorted(u for u in used if u not in dec)
if undeclared:
    hint=" (note: validate reports at most one error per node, so this one was masked)" if "riskBand" in undeclared else ""
    fail("still undeclared: "+", ".join(f"vars.{u}" for u in undeclared)+hint)
print(f"PASS: {len(exprs)} gate expressions preserved; all {len(used)} referenced variables declared")
