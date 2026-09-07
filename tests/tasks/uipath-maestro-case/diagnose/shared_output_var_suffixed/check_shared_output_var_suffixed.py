import json, os, re, sys

CP = "LinearThreeStages/LinearThreeStages/caseplan.json"
SHARED = "lastEmailStatus"

def fail(m): sys.exit(f"FAIL: {m}")

def load():
    if not os.path.isfile(CP): fail(f"{CP} not found")
    try: return json.load(open(CP))
    except Exception as e: fail(f"{CP} is not valid JSON: {e}")

p = load()
stages = [n for n in p.get("nodes", []) if str(n.get("type", "")).endswith("Stage")]
by_label = {(n.get("data") or {}).get("label"): n for n in stages}
for s in ("Intake", "Review", "Decision"):
    if s not in by_label: fail(f"stage '{s}' was deleted; repair the defect, don't remove stages")

def tasks(n):
    out = []
    for lane in (n.get("data") or {}).get("tasks") or []:
        out.extend(lane if isinstance(lane, list) else [lane])
    return out

sends = [t for t in tasks(by_label["Review"]) if t.get("type") == "execute-connector-activity"]
if len(sends) < 2:
    fail(f"Review carries {len(sends)} connector task(s); both send tasks must stay, and the fix is "
         f"not to delete one of them")

# 每个发信任务写状态的那一行
rows = []
for t in sends:
    outs = ((t.get("data") or {}).get("outputs")) or []
    hit = [o for o in outs if SHARED in str(o.get("id") or "") or SHARED in str(o.get("var") or "")]
    if not hit:
        fail(f"task {t.get('displayName')!r} no longer writes a send status; both tasks report into "
             f"the same case variable by design")
    rows.append((t.get("displayName"), hit[0]))

suffixed = [(n, r) for n, r in rows
            if re.fullmatch(SHARED + r"\d+", str(r.get("id") or "")) or
               re.fullmatch(SHARED + r"\d+", str(r.get("var") or ""))]
if suffixed:
    names = [f"{n}: id={r.get('id')!r} var={r.get('var')!r}" for n, r in suffixed]
    fail(f"a send status still lands in a numbered variant of {SHARED!r}: {names}. Both tasks report "
         f"into one case variable, so the case reports the most recent send; a suffix gives each task "
         f"its own name and only the first one reaches the gate")

for n, r in rows:
    if r.get("id") != SHARED or r.get("var") != SHARED:
        fail(f"{n}: the status row is id={r.get('id')!r} var={r.get('var')!r}; both must be {SHARED!r}")
    if r.get("target") != f"={SHARED}":
        fail(f"{n}: the status row's target is {r.get('target')!r}; it must be '={SHARED}'")

decls = [v for grp in (p.get("variables") or {}).values() for v in grp
         if re.fullmatch(SHARED + r"\d*", str(v.get("name") or ""))]
names = sorted(str(v.get("name")) for v in decls)
if names != [SHARED]:
    fail(f"the case declares {names}; there is one shared status variable, and a numbered companion "
         f"declared beside it keeps the split alive")

gates = []
for c in (by_label["Decision"].get("data") or {}).get("entryConditions") or []:
    for rl in c.get("rules") or []:
        for r in rl:
            if r.get("conditionExpression"): gates.append(r["conditionExpression"])
if not any(f"vars.{SHARED}" in g for g in gates):
    fail(f"Decision's gate no longer reads vars.{SHARED}; this repair does not touch the gate")

print("PASS")
