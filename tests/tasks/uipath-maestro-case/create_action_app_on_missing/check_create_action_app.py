"""Grade a Create-on-Missing run for two missing Action Apps.

Checks side effects only: the built Coded Action App projects, their
registration in the .uipx, and the caseplan bindings. Run from the sandbox root.
"""
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

APPS = {
    "Approve Request": {
        "app": "create-probe-approval-app-q93",
        "inputs": {"requestId"},
        "outputs": {"decision"},
        "outcomes": {"Approve", "Reject"},
    },
    "Record Review Notes": {
        "app": "create-probe-review-app-q93",
        "inputs": {"requestId", "decision"},
        "outputs": {"reviewNotes"},
        "outcomes": None,
    },
}


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def files(name):
    return [p for p in ROOT.rglob(name) if ".venv" not in p.parts and "node_modules" not in p.parts]


def actions(node, out):
    if isinstance(node, dict):
        if node.get("type") == "action":
            out.append(node)
        for v in node.values():
            actions(v, out)
    elif isinstance(node, list):
        for v in node:
            actions(v, out)
    return out


plans = [p for p in files("caseplan.case")]
if len(plans) != 1:
    fail(f"expected exactly one caseplan.case, found {len(plans)}")
plan_text = plans[0].read_text(encoding="utf-8")
if "<UNRESOLVED" in plan_text:
    fail("caseplan.case still carries an <UNRESOLVED marker")
plan = json.loads(plan_text)
bindings = {b["id"]: b for b in plan.get("bindings", [])}
tasks = {t.get("displayName"): t for t in actions(plan, [])}

uipx = files("*.uipx")
if len(uipx) != 1:
    fail(f"expected exactly one .uipx, found {len(uipx)}")
uipx_doc = json.loads(uipx[0].read_text(encoding="utf-8"))
registered = {p["ProjectRelativePath"]: p["Type"] for p in uipx_doc.get("Projects", [])}
solution_dir = uipx[0].parent

for display, want in APPS.items():
    app = want["app"]
    task = tasks.get(display)
    if task is None:
        fail(f"no action task named {display!r}")
    data = task.get("data") or {}
    if not data:
        fail(f"{display!r} is a placeholder (empty data block)")
    for field in ("name", "folderPath"):
        ref = str(data.get(field, ""))
        if not ref.startswith("=bindings."):
            fail(f"{display!r} data.{field} is not a binding reference: {ref!r}")
    name_b = bindings.get(data["name"].split(".", 1)[1])
    path_b = bindings.get(data["folderPath"].split(".", 1)[1])
    for b, attr, default in ((name_b, "name", app), (path_b, "folderPath", "")):
        if not b:
            fail(f"{display!r} binding for {attr} missing from bindings[]")
        if b.get("resource") != "app" or b.get("propertyAttribute") != attr:
            fail(f"{display!r} {attr} binding has wrong resource/propertyAttribute: {b}")
        if b.get("resourceKey") != f"solution_folder.{app}":
            fail(f"{display!r} {attr} resourceKey is {b.get('resourceKey')!r}")
        if b.get("default") != default:
            fail(f"{display!r} {attr} default is {b.get('default')!r}, expected {default!r}")
    rec = data.get("recipient")
    if not isinstance(rec, dict) or "Value" not in rec:
        fail(f"{display!r} recipient is not a {{Type, Value}} object")

    rel = f"{app}/project.uiproj"
    if registered.get(rel) != "AppV2":
        fail(f"{rel} is not registered as AppV2 in the .uipx: {registered}")
    schema_path = solution_dir / app / "action-schema.json"
    if not schema_path.is_file():
        fail(f"missing {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    def props(section):
        return set(((schema.get(section) or {}).get("properties") or {}).keys())

    if not want["inputs"] <= props("inputs") | props("inOuts"):
        fail(f"{app} inputs {props('inputs')} lack {want['inputs']}")
    if not want["outputs"] <= props("outputs") | props("inOuts"):
        fail(f"{app} outputs {props('outputs')} lack {want['outputs']}")
    if want["outcomes"] and not want["outcomes"] <= props("outcomes"):
        fail(f"{app} outcomes {props('outcomes')} lack {want['outcomes']}")
    src = [f for f in (solution_dir / app).rglob("*") if f.is_file() and "node_modules" not in f.parts
           and f.suffix in (".tsx", ".ts", ".jsx", ".js", ".html")]
    if not any("completeTask" in f.read_text(encoding="utf-8", errors="ignore") for f in src):
        fail(f"{app} never calls completeTask — its form cannot submit the task")
    decl = solution_dir / "resources" / "solution_folder" / "app" / "codedAction" / f"{app}.json"
    if not decl.is_file():
        fail(f"missing resource declaration {decl}")

print("OK: both action tasks bound to built in-solution Coded Action Apps")
