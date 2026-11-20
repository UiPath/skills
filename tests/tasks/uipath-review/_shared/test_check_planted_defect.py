"""Unit tests for check_planted_defect.py.

The checker grades twenty tasks, so each rule it applies is pinned here: a
defect term counts only when framed as a problem, only near the subject when
one is given, and only while the planted defect is still in the fixture.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_planted_defect.py"
PAD = "\n\n### Per-Project Summary\n" + "Structural counts recorded for the project. " * 15


def run(tmp_path: Path, report: str | None, *args: str) -> subprocess.CompletedProcess:
    if report is not None:
        (tmp_path / "_review_report.md").write_text(report + PAD, encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER), *args], cwd=tmp_path,
                          capture_output=True, text=True)


def test_flagged_defect_passes(tmp_path):
    r = run(tmp_path, "| C-001 | Main.xaml: hardcoded password in Invoke Code. |",
            "--flag", "hardcod|plaintext", "--mention", "password")
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stdout


def test_negated_presence_defect_fails(tmp_path):
    r = run(tmp_path, "No hardcoded password was found in the workflow.", "--flag", "hardcod")
    assert r.returncode != 0
    assert "does not flag the defect" in r.stderr


def test_absence_defect_accepts_negation_as_the_finding(tmp_path):
    r = run(tmp_path, "ClaimsAudit is not listed in the .uipx.",
            "--subject", "ClaimsAudit", "--flag-absence", "not listed|orphan")
    assert r.returncode == 0, r.stderr


def test_dismissed_absence_defect_fails(tmp_path):
    r = run(tmp_path, "ClaimsAudit: no orphan issues, the project is registered.",
            "--subject", "ClaimsAudit", "--flag-absence", "orphan")
    assert r.returncode != 0


def test_subject_must_be_named(tmp_path):
    r = run(tmp_path, "One project is an orphan.", "--subject", "ClaimsAudit",
            "--flag-absence", "orphan")
    assert r.returncode != 0
    assert "does not name the affected item" in r.stderr


def test_term_far_from_subject_does_not_count(tmp_path):
    report = "ClaimsAudit runs nightly." + " filler" * 200 + " A different project is an orphan."
    r = run(tmp_path, report, "--subject", "ClaimsAudit", "--flag-absence", "orphan")
    assert r.returncode != 0


def test_every_flag_group_is_required(tmp_path):
    r = run(tmp_path, "Parallel gateway Gw_Split is used.", "--mention", "parallel",
            "--mention", "exclusive")
    assert r.returncode != 0
    assert "exclusive" in r.stderr


def test_marker_removed_from_fixture_fails(tmp_path):
    (tmp_path / "Main.xaml").write_text("clean", encoding="utf-8")
    r = run(tmp_path, "Hardcoded password in Main.xaml.", "--marker", "Main.xaml::FAKE_SECRET",
            "--flag", "hardcod")
    assert r.returncode != 0
    assert "fixture appears mutated" in r.stderr


def test_marker_present_passes(tmp_path):
    (tmp_path / "Main.xaml").write_text("x FAKE_SECRET y", encoding="utf-8")
    r = run(tmp_path, "Hardcoded password in Main.xaml.", "--marker", "Main.xaml::FAKE_SECRET",
            "--flag", "hardcod")
    assert r.returncode == 0, r.stderr


def test_marker_absent_path_created_fails(tmp_path):
    (tmp_path / "LoanNotify").mkdir()
    r = run(tmp_path, "LoanNotify is missing.", "--marker-absent", "LoanNotify",
            "--subject", "LoanNotify", "--flag-absence", "missing")
    assert r.returncode != 0
    assert "now exists" in r.stderr


def test_missing_or_short_report_fails(tmp_path):
    assert run(tmp_path, None, "--flag", "x").returncode != 0
    (tmp_path / "_review_report.md").write_text("hardcoded", encoding="utf-8")
    r = subprocess.run([sys.executable, str(CHECKER), "--flag", "hardcod"], cwd=tmp_path,
                       capture_output=True, text=True)
    assert r.returncode != 0
    assert "suspiciously short" in r.stderr
