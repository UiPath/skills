import json, os, sys

CP = "LinearThreeStages/LinearThreeStages/caseplan.json"
GATE_VAR = "reviewOutcome"

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
if not acts: fail("the action task in Review was deleted or retyped; the fix must keep it and repair its data")
task = acts[0]
d = task.get("data") or {}

# 绑定必须原样：这是一处字段的修复，不是重新解析资源
bound = {b.get("id"): b for b in (p.get("bindings") or [])}
for field in ("name", "folderPath"):
    v = str(d.get(field) or "")
    if not v.startswith("=bindings."):
        fail(f"data.{field} is {v!r}; the app was already resolved and its binding must stay")
    if v.split(".", 1)[1] not in bound:
        fail(f"data.{field} points at {v!r}, which no top-level binding declares")

catalog = d.get("actionCatalogName")
if catalog is not None:
    keys = {str(b.get("resourceKey") or "") for b in (p.get("bindings") or [])}
    names = {str(b.get("default") or "") for b in (p.get("bindings") or [])}
    if catalog not in names and not any(str(catalog) in k for k in keys):
        fail(f"actionCatalogName is {catalog!r}, which no bound resource declares. "
             f"The field is optional and must be omitted unless a real action catalog is named; "
             f"an action type inside an app is not a catalog")

if not d.get("taskTitle"):
    fail("data.taskTitle was removed; the validator rejects a resolved action task without one")
if not (d.get("recipient") or {}).get("Type") and (d.get("recipient") or {}).get("Type") != 0:
    fail("data.recipient lost its Type; the task must still say who answers it")

outs = d.get("outputs") or []
rows = [o for o in outs if o.get("id") == GATE_VAR]
if not rows:
    fail(f"the output row writing {GATE_VAR} was changed or removed; this repair does not touch the outputs")

gates = []
for c in (by_label["Decision"].get("data") or {}).get("entryConditions") or []:
    for rl in c.get("rules") or []:
        for r in rl:
            if r.get("conditionExpression"): gates.append(r["conditionExpression"])
if not any(f"vars.{GATE_VAR}" in g for g in gates):
    fail(f"Decision's gate no longer reads vars.{GATE_VAR}; this repair does not touch the gate")

print("PASS")
