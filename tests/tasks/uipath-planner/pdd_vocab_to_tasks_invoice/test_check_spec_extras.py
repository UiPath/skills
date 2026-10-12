"""check_spec_extras.py: an ideal tasks file scores 1.0; missing choice-set tasks or unblocked VDO tasks lower only their component."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_spec_extras.py"
GOLDEN = HERE / "golden.json"
SPEC = HERE / "fixtures" / "vocabulary" / "entities.json"


def ideal_tasks(drop_choicesets: bool = False, unblock_vdos: bool = False) -> str:
    spec = json.loads(SPEC.read_text())
    out, n, ids = ["# Invoice Processing — tasks", ""], 0, {}

    def task(ident, status="[ ] pending", blocked=(), reason=None, body=None):
        nonlocal n
        n += 1
        out.extend([f"## Task T{n} — uipath-platform — {ident.split(':')[-1]}", f"**Identity:** `{ident}`",
                    f"**Status:** {status}", f"**Blocked by:** {', '.join(blocked) or 'none'}"])
        if reason:
            out.append(f"**Blocked reason:** {reason}")
        if body is not None:
            out.extend(["```json", json.dumps(body), "```"])
        out.append("")
        return f"T{n}"

    if not drop_choicesets:
        for c in spec["choiceSets"]:
            ids[c["name"]] = task(f"platform:Invoice:choiceset:{c['name']}", body={"name": c["name"], "values": c["values"]})
    for e in spec["entities"]:
        if e["class"] == "VDO":
            if unblock_vdos:
                task(f"platform:Invoice:entity:{e['name']}", body=e["body"])
            else:
                task(f"platform:Invoice:entity:{e['name']}", status="[!] blocked", reason=e["blockedReason"], body=e["body"])
        else:
            task(f"platform:Invoice:entity:{e['name']}", blocked=[ids[c["name"]] for c in e.get("choiceSets", []) if c["name"] in ids],
                 body=e["body"])
    return "\n".join(out)


def run(tmp_path: Path, text: str) -> tuple[float, str]:
    p = tmp_path / "invoice-processing-tasks.md"
    p.write_text(text)
    r = subprocess.run([sys.executable, str(CHECKER), "--golden", str(GOLDEN), "--tasks", str(p)], capture_output=True, text=True)
    lines = r.stdout.splitlines()
    return float(lines[0]), "\n".join(lines[1:])


def test_ideal_tasks_score_one(tmp_path):
    s, d = run(tmp_path, ideal_tasks())
    assert s == pytest.approx(1.0), d


def test_missing_tasks_file_scores_zero(tmp_path):
    r = subprocess.run([sys.executable, str(CHECKER), "--golden", str(GOLDEN), "--tasks", str(tmp_path / "none.md")],
                       capture_output=True, text=True)
    assert float(r.stdout.splitlines()[0]) == 0.0


def test_missing_choiceset_tasks_lower_only_choicesets(tmp_path):
    s, d = run(tmp_path, ideal_tasks(drop_choicesets=True))
    assert "choicesets 0.00" in d and "blocked 1.00" in d, d
    assert s == pytest.approx(0.5)


def test_unblocked_vdo_tasks_lower_only_blocked(tmp_path):
    s, d = run(tmp_path, ideal_tasks(unblock_vdos=True))
    assert "choicesets 1.00" in d and "blocked 0.00" in d, d
    assert s == pytest.approx(0.5)
