import json, os, re, sys

CP = "LinearThreeStages/LinearThreeStages/caseplan.json"
# 连接器活动上这四个是可选的，未用时留空是对的
OPTIONAL = {"body", "file", "pathParameters", "queryParameters"}

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

acts = [t for t in tasks(by_label["Review"]) if t.get("type") == "action"]
if not acts: fail("the action task in Review was deleted or retyped; the fix must keep it and bind its inputs")
task = acts[0]
ins = ((task.get("data") or {}).get("inputs")) or []
if len(ins) < 3:
    fail(f"the task declares {len(ins)} input(s); its three schema inputs stay on the task. "
         f"Deleting an input is not the same as binding it")

blank = [i.get("name") for i in ins if i.get("name") not in OPTIONAL and not i.get("value")]
if blank:
    fail(f"{blank} carry no value; an input's binding is its `value`, and a slot minted with an empty "
         f"value reaches the activity as nothing. Write the expression the case supplies")

# 已知的可用来源，防止编造一个字面量糊过去
known = set()
for grp in (p.get("variables") or {}).values():
    for v in grp: known.add(str(v.get("name") or ""))
for n in stages:
    for t in tasks(n):
        for o in ((t.get("data") or {}).get("outputs") or []):
            known.add(str(o.get("id") or ""))

for i in ins:
    if i.get("name") in OPTIONAL: continue
    v = str(i.get("value") or "")
    if not v.startswith("="):
        fail(f"input {i.get('name')!r} carries {v!r}; a literal invented here is not what the case "
             f"supplies. Bind it to a case variable or an upstream output")
    refs = re.findall(r"vars\.([A-Za-z_][A-Za-z0-9_]*)", v)
    unknown = [r for r in refs if r not in known]
    if unknown:
        fail(f"input {i.get('name')!r} reads {unknown}, which nothing in the case declares or produces")
    for field in ("id", "var", "elementId"):
        if not i.get(field):
            fail(f"input {i.get('name')!r} lost its {field}; binding sets `value` and leaves the slot alone")

if not (task.get("data") or {}).get("taskTitle"):
    fail("data.taskTitle was removed; the validator rejects a resolved action task without one")

gates = []
for c in (by_label["Decision"].get("data") or {}).get("entryConditions") or []:
    for rl in c.get("rules") or []:
        for r in rl:
            if r.get("conditionExpression"): gates.append(r["conditionExpression"])
if not any("vars.reviewOutcome" in g for g in gates):
    fail("Decision's gate no longer reads vars.reviewOutcome; this repair does not touch the gate")

print("PASS")
