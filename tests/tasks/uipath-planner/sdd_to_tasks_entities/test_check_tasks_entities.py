"""check_tasks_entities.py: a tasks file mirroring the golden scores 1.0; each defect lowers only its component."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_tasks_entities.py"
GOLDEN = HERE / "golden.json"


def tasks_from_golden(g: dict) -> str:
    out = ["# Student Club Insights — tasks", "", "Source SDD: student-club-insights-sdd.md · SDD scope: single-product · Execution autonomy: autonomous", ""]
    n = 0; ids = {}
    order = sorted(g["entities"], key=lambda e: len(e["relationships"]))  # targets first
    for e in order:
        n += 1; ids[e["name"]] = f"T{n}"
        fields = []
        for f in e["fields"]:
            rel = next((r for r in e["relationships"] if r["field"] == f["name"]), None)
            if rel:
                fields.append({"name": f["name"], "type": "RELATIONSHIP", "referenceEntity": rel["referenceEntity"], "referenceField": rel["referenceField"]})
            else:
                fields.append({"name": f["name"], "type": f["type"], "isRequired": f["isRequired"]})
        blocked = ", ".join(ids[r["referenceEntity"]] for r in e["relationships"] if r["referenceEntity"] in ids) or "none"
        body = json.dumps({"displayName": e["name"], "description": f"{e['name']} record", "fields": fields}, indent=1)
        out += [f"## Task T{n} — uipath-platform — Create Native entity {e['name']}", "", f"**Identity:** `platform:StudentClubInsights:entity:{e['name']}`", "**Status:** [ ] pending", f"**Blocked by:** {blocked}", "**Skill prompt:**", "", f"> Create the Native Data Fabric entity `{e['name']}` in folder Shared with this body:", "", "```json", body, "```", "", "- [ ] preview then confirm", "- [ ] **Validate:** `uip df entities get`", ""]
    for e in order:
        n += 1
        out += [f"## Task T{n} — uipath-solution — Declare entity {e['name']} as a solution resource", "", f"**Identity:** `solution:StudentClubInsights:resources:Entity:{e['name']}`", "**Status:** [ ] pending", f"**Blocked by:** {ids[e['name']]}", "**Skill prompt:**", "", f"> uip solution resources add --source remote --kind Entity --name {e['name']} --folder-path Shared", "", "- [ ] **Validate:** resource listed", ""]
    for c in g["consumers"]:
        n += 1
        ents = "; ".join(f"{k} ({v}) — {c['where'][k]}" for k, v in c["entities"].items())
        blocked = ", ".join(ids[k] for k in c["entities"])
        out += [f"## Task T{n} — {c['skill']} — Build the ExpenseApproval flow", "", f"**Identity:** `{c['skill']}:{c['project']}:ExpenseApproval.flow`", "**Status:** [ ] pending", f"**Blocked by:** {blocked}", f"**Entities:** {ents}", "**Skill prompt:**", "", "> Build the flow per §3 of the SDD. Bind reads by entity name.", "", "- [ ] **Validate:** flow validate", ""]
    return "\n".join(out)


def run(path: Path) -> tuple[float, str]:
    r = subprocess.run([sys.executable, str(CHECKER), "--golden", str(GOLDEN), "--tasks", str(path)], capture_output=True, text=True)
    lines = r.stdout.splitlines(); return float(lines[0]), "\n".join(lines[1:])


@pytest.fixture()
def golden() -> dict:
    return json.loads(GOLDEN.read_text())


def test_perfect_tasks_score_one(tmp_path, golden):
    p = tmp_path / "x-tasks.md"; p.write_text(tasks_from_golden(golden)); s, d = run(p)
    assert s == pytest.approx(1.0, abs=1e-6), d


def test_no_tasks_file_scores_zero(tmp_path):
    p = tmp_path / "x-tasks.md"; p.write_text("# nothing\n"); s, d = run(p)
    assert s == 0.0, d


def test_missing_binding_lowers_only_bindings_and_order(tmp_path, golden):
    import re
    text = re.sub(r"^\*\*Entities:\*\* .*$", "**Entities:** none", tasks_from_golden(golden), flags=re.M)
    p = tmp_path / "x-tasks.md"; p.write_text(text); s, d = run(p)
    assert s < 1.0 and "entities bound, directions right 0/3" in d and "[entities] core 5/5" in d, d


def test_wrong_direction_lowers_bindings(tmp_path, golden):
    text = tasks_from_golden(golden).replace("Expense (read-write)", "Expense (read)")
    p = tmp_path / "x-tasks.md"; p.write_text(text); s, d = run(p)
    assert 0.85 < s < 1.0 and "directions right 2/3" in d, d


def test_dropped_entity_task_lowers_entities(tmp_path, golden):
    text = tasks_from_golden(golden).replace("`platform:StudentClubInsights:entity:Member`", "`platform:StudentClubInsights:entity:Sponsor`")
    p = tmp_path / "x-tasks.md"; p.write_text(text); s, d = run(p)
    assert s < 1.0 and "unmatched entity tasks 1" in d, d


def test_blockquoted_body_and_transitive_order_score_full(tmp_path, golden):
    """The planner writes the create body inside the Skill prompt blockquote and blocks the consumer on the
    resource tasks (which are blocked by the entity tasks) — both must read as the contract."""
    import re
    text = tasks_from_golden(golden)
    # quote every fenced json body
    text = re.sub(r"```json\n(.*?)\n```", lambda m: "> ```json\n" + "\n".join("> " + l for l in m.group(1).splitlines()) + "\n> ```", text, flags=re.S)
    # consumer blocked by the resource tasks instead of the entity tasks
    ids = {m.group(2): m.group(1) for m in re.finditer(r"## Task (T\d+) — uipath-solution — Declare entity (\w+)", text)}
    ents = {m.group(2): m.group(1) for m in re.finditer(r"## Task (T\d+) — uipath-platform — Create Native entity (\w+)", text)}
    for c in golden["consumers"]:
        old = ", ".join(ents[k] for k in c["entities"]); new = ", ".join(ids[k] for k in c["entities"])
        text = text.replace(f"**Blocked by:** {old}\n**Entities:**", f"**Blocked by:** {new}\n**Entities:**")
    p = tmp_path / "x-tasks.md"; p.write_text(text); s, d = run(p)
    assert s == pytest.approx(1.0, abs=1e-6), d
