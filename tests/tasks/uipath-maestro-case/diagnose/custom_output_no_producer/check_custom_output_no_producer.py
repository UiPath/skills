import json, os, sys

CP = "LinearThreeStages/LinearThreeStages/caseplan.json"
GATE_VAR = "lastEmailStatus"

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

conn = [t for t in tasks(by_label["Review"]) if t.get("type") == "execute-connector-activity"]
if not conn: fail("the connector task in Review was deleted or retyped; the fix must keep it and repair its output row")
task = conn[0]
outs = ((task.get("data") or {}).get("outputs")) or []

rows = [o for o in outs if o.get("var") == GATE_VAR or o.get("id") == GATE_VAR]
if not rows: fail(f"no output row carries {GATE_VAR}; the row that feeds the gate was removed")
row = rows[0]

# Every other output row on this task carries `id` and `target`; the custom row is the only
# one missing both. The shapes are documented side by side, so the repaired row must match
# its siblings rather than stay the one exception.
siblings = [o for o in outs if o is not row]
if siblings and all(s.get("id") and s.get("target") for s in siblings):
    if not row.get("id"):
        fail(f"the row's id is {row.get('id')!r} while every other output row on this task carries one; "
             f"the row must declare the variable it writes")
    if row.get("target") != f"={GATE_VAR}":
        fail(f"the row's target is {row.get('target')!r} while its siblings all carry one; "
             f"it must be '={GATE_VAR}'")
if row.get("id") and row.get("id") != GATE_VAR:
    fail(f"the row's id is {row.get('id')!r}; it must name the variable the row writes, {GATE_VAR!r}")
if "js:vars." in str(row.get("source") or ""):
    fail(f"the row's source is {row.get('source')!r}; it reads the case variable it is supposed to write. "
         f"It must read the connector response, e.g. '=response.status'")
if row.get("elementId") == "root":
    fail("the row's elementId is 'root'; it must name the stage and task that produce it")

decls = [v for grp in (p.get("variables") or {}).values() for v in grp if v.get("name") == GATE_VAR]
if not decls: fail(f"{GATE_VAR} is no longer declared on the case")
if decls[0].get("default"):
    fail(f"{GATE_VAR} was given the default {decls[0]['default']!r}; that opens the gate without the task ever writing it")

gates = []
for c in (by_label["Decision"].get("data") or {}).get("entryConditions") or []:
    for rl in c.get("rules") or []:
        for r in rl:
            if r.get("conditionExpression"): gates.append(r["conditionExpression"])
if not gates: fail("Decision's entry gate was deleted; the fix must keep the case gated on the email status")
if not any(f"vars.{GATE_VAR}" in g for g in gates):
    fail(f"Decision's gate no longer reads vars.{GATE_VAR}; it must still gate on what the connector writes")

print("PASS")
