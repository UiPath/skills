import json
import subprocess
import sys
from pathlib import Path

CHECK = Path(__file__).with_name("check_create_action_app.py")
APPS = {
    "Approve Request": ("create-probe-approval-app-q93", {"requestId"}, {"decision"}, {"Approve": {}, "Reject": {}}),
    "Record Review Notes": ("create-probe-review-app-q93", {"requestId", "decision"}, {"reviewNotes"}, {"Done": {}}),
}


def build(root, *, placeholder=False, drop_decl=False, no_submit=False):
    sol = root / "Sol"
    projects, bindings, tasks = [], [], []
    for i, (display, (app, ins, outs, outcomes)) in enumerate(APPS.items()):
        (sol / app).mkdir(parents=True)
        schema = {
            "inputs": {"properties": {k: {} for k in ins}},
            "outputs": {"properties": {k: {} for k in outs}},
            "inOuts": {"properties": {}},
            "outcomes": {"properties": outcomes},
        }
        (sol / app / "action-schema.json").write_text(json.dumps(schema))
        (sol / app / "source").mkdir()
        (sol / app / "source" / "App.tsx").write_text("" if no_submit else "service.completeTask(x)")
        decl = sol / "resources/solution_folder/app/codedAction"
        decl.mkdir(parents=True, exist_ok=True)
        if not (drop_decl and i == 1):
            (decl / f"{app}.json").write_text("{}")
        projects.append({"Type": "AppV2", "ProjectRelativePath": f"{app}/project.uiproj", "Id": str(i)})
        for attr, default in (("name", app), ("folderPath", "")):
            bindings.append({"id": f"{'n' if attr == 'name' else 'f'}{i}", "name": attr, "resource": "app",
                             "resourceKey": f"solution_folder.{app}", "default": default,
                             "propertyAttribute": attr})
        data = {} if placeholder and i == 1 else {
            "name": f"=bindings.n{i}", "folderPath": f"=bindings.f{i}",
            "recipient": {"Type": 2, "Value": "a@example.com"}}
        tasks.append({"type": "action", "displayName": display, "data": data})
    (sol / "Sol.uipx").write_text(json.dumps({"Projects": projects}))
    (sol / "Case").mkdir()
    (sol / "Case/caseplan.case").write_text(json.dumps({"bindings": bindings, "nodes": [{"data": {"tasks": [tasks]}}]}))


def run(root):
    return subprocess.run([sys.executable, str(CHECK), str(root)], capture_output=True, text=True)


def test_pass(tmp_path):
    build(tmp_path)
    r = run(tmp_path)
    assert r.returncode == 0, r.stdout


def test_placeholder_fails(tmp_path):
    build(tmp_path, placeholder=True)
    r = run(tmp_path)
    assert r.returncode == 1 and "placeholder" in r.stdout


def test_missing_declaration_fails(tmp_path):
    build(tmp_path, drop_decl=True)
    r = run(tmp_path)
    assert r.returncode == 1 and "resource declaration" in r.stdout


def test_form_without_complete_task_fails(tmp_path):
    build(tmp_path, no_submit=True)
    r = run(tmp_path)
    assert r.returncode == 1 and "completeTask" in r.stdout
