"""Unit tests for check_interview.mjs, the grader of the interview tasks: each subcommand passes on the
state a task expects and fails on the state it guards against. The grader is Node; these tests drive it
through `node`, so the CI job needs Node >= 20 on the runner.

Run: pytest tests/tasks/uipath-planner/interview/_shared/test_check_interview.py -v
"""

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
GRADER = HERE / "check_interview.mjs"
GENOME = HERE.parent / "interview_genome" / "fixtures" / "supplier-invoice-entry-and-approval-genome.md"
SDD = HERE.parent / "interview_sdd" / "fixtures" / "supplier-invoice-entry-sdd.md"


def grade(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["node", str(GRADER), *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8")


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    shutil.copy(GENOME, tmp_path)
    shutil.copy(SDD, tmp_path)
    return tmp_path


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_absent_passes_with_no_match_and_fails_naming_the_file(sandbox):
    assert grade(sandbox, "absent", r"-readiness\.md$").returncode == 0
    r = grade(sandbox, "absent", r"sdd(\.draft)?\.md$")
    assert r.returncode == 1 and "supplier-invoice-entry-sdd.md" in r.stdout


def test_absent_skips_dot_folders(sandbox):
    (sandbox / ".venv").mkdir()
    (sandbox / ".venv" / "x-genome.md").write_text("x", encoding="utf-8")
    (sandbox / "supplier-invoice-entry-and-approval-genome.md").unlink()
    assert grade(sandbox, "absent", r"-genome\.md$").returncode == 0


def test_strict_runs_the_skill_checker_at_the_genome_level(sandbox):
    (sandbox / "supplier-invoice-entry-sdd.md").unlink()
    r = grade(sandbox, "strict")
    assert r.returncode == 0, r.stdout + r.stderr


def test_strict_fails_with_no_genome_or_two(tmp_path):
    assert grade(tmp_path, "strict").returncode == 1
    (tmp_path / "a-genome.md").write_text("x", encoding="utf-8")
    (tmp_path / "b-genome.md").write_text("x", encoding="utf-8")
    assert "found 2" in grade(tmp_path, "strict").stdout


def test_line_matches_any_genome_line(sandbox):
    assert grade(sandbox, "line", r"^\s*\d+\.[^\n]*\blimit\b[^\n]*default: none").returncode == 0
    assert grade(sandbox, "line", r"limit[^\n]*default: 10 ?000").returncode == 1


def test_entries_reads_open_and_decided(sandbox):
    genome = sandbox / "supplier-invoice-entry-and-approval-genome.md"
    assert grade(sandbox, "entries", genome.name, "open", "1-12").returncode == 0
    text = genome.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^5\. (.*?\?) \(business outcome;.*$", r"5. \1 (decided 2026-01-02: no)", text)
    genome.write_text(text, encoding="utf-8")
    assert grade(sandbox, "entries", genome.name, "decided", "5").returncode == 0
    r = grade(sandbox, "entries", genome.name, "open", "4-6")
    assert r.returncode == 1 and "D5 is decided" in r.stdout
    assert "D13 is missing" in grade(sandbox, "entries", genome.name, "open", "13").stdout


def test_items_reads_blank_answered_and_gone(sandbox):
    sdd = sandbox / "supplier-invoice-entry-sdd.md"
    assert grade(sandbox, "items", sdd.name, "blank", "D1-11").returncode == 0
    text = sdd.read_text(encoding="utf-8").replace(
        "- **Answer (by the process owner):**\n\n**D2.", "- **Answer (by the process owner):** default\n\n**D2.", 1)
    sdd.write_text(text, encoding="utf-8")
    assert grade(sandbox, "items", sdd.name, "answered", "D1").returncode == 0
    assert grade(sandbox, "items", sdd.name, "answered", "D12").returncode == 0
    r = grade(sandbox, "items", sdd.name, "blank", "D1")
    assert r.returncode == 1 and 'D1 is answered "default"' in r.stdout
    assert grade(sandbox, "items", sdd.name, "blank", "X1").returncode == 2


def test_items_reads_a_readiness_file(tmp_path):
    readiness = HERE.parent / "apply_readiness" / "fixtures" / "ecb-fx-rates-readiness.md"
    shutil.copy(readiness, tmp_path)
    assert grade(tmp_path, "items", readiness.name, "answered", "D2", "CQ4-5", "R1").returncode == 0
    assert grade(tmp_path, "items", readiness.name, "blank", "D1", "D3-4", "CQ1-3", "CQ6-8", "R2-6").returncode == 0


def test_count_needs_the_minimum(sandbox):
    assert grade(sandbox, "count", SDD.name, r"Interview: \d+ points?", "1").returncode == 0
    assert grade(sandbox, "count", SDD.name, r"Interview: \d+ points?", "2").returncode == 1


def test_unchanged_and_body_hash_with_lf_endings(sandbox):
    sdd = sandbox / SDD.name
    text = sdd.read_text(encoding="utf-8")
    body = text[text.index("<!-- planner-sdd-body:v1 -->"):]
    assert grade(sandbox, "body", sdd.name, sha(body)).returncode == 0
    assert grade(sandbox, "unchanged", sdd.name, sha(text)).returncode == 0
    sdd.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    assert grade(sandbox, "unchanged", sdd.name, sha(text)).returncode == 0
    r = grade(sandbox, "body", sdd.name, "0" * 64)
    assert r.returncode == 1 and sha(body) in r.stdout


def test_usage_errors_exit_2(sandbox):
    assert grade(sandbox, "bogus").returncode == 2
    assert grade(sandbox, "entries", GENOME.name, "closed", "1").returncode == 2
