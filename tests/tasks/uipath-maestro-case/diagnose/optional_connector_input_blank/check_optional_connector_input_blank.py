import json, os, sys

CP = "LinearThreeStages/LinearThreeStages/caseplan.json"
OPTIONAL = ("body", "file", "pathParameters", "queryParameters")

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
if not conn: fail("the connector task in Review was deleted or retyped; the fix must keep it and repair its inputs")
task = conn[0]
ins = ((task.get("data") or {}).get("inputs")) or []
by_name = {i.get("name"): i for i in ins}

missing = [n for n in OPTIONAL if n not in by_name]
if missing:
    fail(f"the connector task no longer declares {missing}; the activity's schema fields stay on the task. "
         f"Deleting an input is not the same as leaving it unset")

if by_name["file"].get("value") == "":
    fail("`file` still carries an empty string; Integration Services reads that as a multipart attachment "
         "with no content and answers 400 'Unable to parse multipart body'. An unused optional input must be null")
if by_name["file"].get("value") is not None:
    fail(f"`file` now carries {by_name['file'].get('value')!r}; nothing in the case supplies a file, so it must "
         f"be null rather than a value invented to get past the error")

if not by_name["body"].get("value"):
    fail("`body` lost its value; the message the task sends is the one input this task genuinely needs")

for n in OPTIONAL:
    row = by_name[n]
    for field in ("id", "var", "elementId"):
        if not row.get(field):
            fail(f"{n} lost its {field}; the slot stays minted even when the value is null")

outs = ((task.get("data") or {}).get("outputs")) or []
rows = [o for o in outs if o.get("id") == "lastEmailStatus"]
if not rows:
    fail("the output row that writes lastEmailStatus was changed or removed; this repair does not touch the outputs")

gates = []
for c in (by_label["Decision"].get("data") or {}).get("entryConditions") or []:
    for rl in c.get("rules") or []:
        for r in rl:
            if r.get("conditionExpression"): gates.append(r["conditionExpression"])
if not any("vars.lastEmailStatus" in g for g in gates):
    fail("Decision's gate no longer reads vars.lastEmailStatus; this repair does not touch the gate")

print("PASS")
