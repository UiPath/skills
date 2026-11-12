"""Guard: uipath-planner's sdd-fingerprint.mjs and uipath-genome's checker agree.

The planner records an SDD's fingerprint on a genome's `Designed in:` line; the builder's checker
recomputes it to tell whether the SDD changed. Each skill carries its own copy of the rule, so this
test fails the moment the two drift.

    python3 -m pytest tests/tasks/uipath-planner/_shared/test_sdd_fingerprint.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
PLANNER = REPO / "skills" / "uipath-planner" / "scripts" / "sdd-fingerprint.mjs"
CHECKER = REPO / "skills" / "uipath-genome" / "scripts" / "check-genome.mjs"

SDDS = {
    "lf": "# SDD\n\n## Planner Handoff\n\n| **Status** | ready |\n| **Tasks file** | `x-tasks.md` (written by `plan`) |\n",
    "crlf-bom-genome-row": "﻿# SDD\r\n\r\n| **Status** | ready |\r\n| **Genome** | `x-genome.md` |\r\n## 1. Overview\r\n",
    "no-handoff": "# SDD\n\nBody only.\n",
}


def planner(path: Path) -> str:
    return subprocess.run(["node", str(PLANNER), str(path)], capture_output=True, text=True, check=True).stdout.strip()


def checker(path: Path) -> str:
    script = (f"import {{ sddFingerprint }} from {json.dumps(CHECKER.as_uri())};"
              f"process.stdout.write(String(sddFingerprint({json.dumps(str(path))})));")
    return subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout


@pytest.mark.parametrize("name", SDDS)
def test_planner_and_checker_fingerprints_agree(tmp_path, name):
    sdd = tmp_path / f"{name}.md"
    sdd.write_bytes(SDDS[name].encode("utf-8"))
    assert planner(sdd) == checker(sdd)


def test_late_handoff_rows_leave_the_fingerprint_unchanged(tmp_path):
    sdd = tmp_path / "x-sdd.md"
    sdd.write_text("# SDD\n\n| **Status** | ready |\n", encoding="utf-8")
    before = planner(sdd)
    sdd.write_text("# SDD\n\n| **Status** | ready |\n| **Tasks file** | `x-tasks.md` |\n| **Genome** | `x-genome.md` |\n", encoding="utf-8")
    assert planner(sdd) == before


def test_unreadable_sdd_is_a_usage_error(tmp_path):
    r = subprocess.run(["node", str(PLANNER), str(tmp_path / "missing.md")], capture_output=True, text=True)
    assert r.returncode == 1 and "cannot read" in r.stderr


ROOT_SDD = """# Claims Solution SDD

## Planner Handoff

| **Status** | ready |
| **SDD scope** | solution |
| **Solution root SDD** | `claims-solution-sdd.md` |
| **Project SDD role** | root |

## Per-Project SDD Index

| SDD | Scope |
|---|---|
| [Intake](projects/intake-sdd.md) | reads the claims |
| `review-sdd.md` | reviews them |
| [Intake again](projects/intake-sdd.md#overview) | listed twice |
"""


def solution(tmp_path: Path) -> Path:
    (tmp_path / "projects").mkdir()
    (tmp_path / "projects" / "intake-sdd.md").write_text("# Intake\n\n| **Project SDD role** | child |\n", encoding="utf-8")
    (tmp_path / "review-sdd.md").write_text("# Review\r\n\r\n| **Project SDD role** | child |\r\n", encoding="utf-8")
    root = tmp_path / "claims-solution-sdd.md"
    root.write_text(ROOT_SDD, encoding="utf-8")
    return root


def test_solution_fingerprint_covers_every_child_in_order(tmp_path):
    root = solution(tmp_path)
    fingerprint = planner(root)
    assert fingerprint == checker(root)
    texts = [root, tmp_path / "projects" / "intake-sdd.md", tmp_path / "review-sdd.md"]
    expected = hashlib.sha256(b"".join(p.read_bytes().replace(b"\r\n", b"\n") for p in texts)).hexdigest()
    assert fingerprint == expected


def test_a_child_change_changes_the_solution_fingerprint_and_the_genome_row_does_not(tmp_path):
    root = solution(tmp_path)
    before = planner(root)
    root.write_text(ROOT_SDD.replace("| **Project SDD role** | root |\n", "| **Project SDD role** | root |\n| **Genome** | `claims-genome.md` |\n"), encoding="utf-8")
    assert planner(root) == checker(root) == before
    (tmp_path / "review-sdd.md").write_text("# Review\n\nRevised.\n", encoding="utf-8")
    assert planner(root) == checker(root) != before


def test_a_missing_child_leaves_the_solution_fingerprint_uncomputed(tmp_path):
    root = solution(tmp_path)
    (tmp_path / "review-sdd.md").unlink()
    r = subprocess.run(["node", str(PLANNER), str(root)], capture_output=True, text=True)
    assert r.returncode == 1 and "child SDD" in r.stderr and "review-sdd.md" in r.stderr
    assert checker(root) == "null"
