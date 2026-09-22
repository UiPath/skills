"""Unit tests for check_review_history.py.

The checker's verdict tracks two artifacts -- the CLI-owned review-history.json
and the report's final-grade footer -- never the shape of the agent's shell
calls. The CLI probe (used only when the history file is missing) is driven
through a stubbed `uip` via the `UIP` env var, exactly like the provenance
checker's tests.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_review_history.py"

PROJECT = "ReviewSol/SampleAgent"

REPORT = textwrap.dedent(
    """\
    # Review Report — ReviewSol / SampleAgent

    ## Summary

    - **Agent Grade:** C

    ## Warning Findings

    | ID | Rule | Finding |
    |---|---|---|
    | W-J-001 | `LC_TOOL_OVERLAP` | Interchangeable tools. Merge them. |

    **Final grade: C**
    """
)

ENTRY = {"grade": "C", "runAt": "2026-09-03T14:02:35.127Z", "errors": 1, "warnings": 2}


def _fake_uip(tmp_path: Path, *, exit_code: int) -> Path:
    launcher = tmp_path / "fake_uip"
    launcher.write_text(f"#!/bin/sh\nexit {exit_code}\n", encoding="utf-8")
    launcher.chmod(0o755)
    return launcher


def _write_history(tmp_path: Path, payload: object) -> None:
    project = tmp_path / PROJECT
    project.mkdir(parents=True, exist_ok=True)
    body = payload if isinstance(payload, str) else json.dumps(payload)
    (project / "review-history.json").write_text(body, encoding="utf-8")


def run(tmp_path: Path, report: str | None = REPORT, uip: Path | None = None) -> subprocess.CompletedProcess:
    if report is not None:
        (tmp_path / "_review_report.md").write_text(report, encoding="utf-8")
    env = {**os.environ, "UIP": str(uip) if uip else "uip-that-does-not-exist"}
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=tmp_path, env=env, capture_output=True, text=True,
    )


# --- the grade was recorded --------------------------------------------------

def test_passes_when_recorded_grade_matches_final_grade(tmp_path):
    _write_history(tmp_path, [ENTRY])
    r = run(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "records grade C" in r.stdout


def test_last_entry_wins_when_history_has_multiple_entries(tmp_path):
    older = {**ENTRY, "grade": "F", "runAt": "2026-09-01T00:00:00.000Z"}
    _write_history(tmp_path, [older, ENTRY])
    r = run(tmp_path)
    assert r.returncode == 0, r.stderr


def test_fails_when_recorded_grade_differs_from_final_grade(tmp_path):
    _write_history(tmp_path, [{**ENTRY, "grade": "A"}])
    r = run(tmp_path)
    assert r.returncode != 0
    assert "does not match the report's final grade" in r.stderr


# --- entry shape --------------------------------------------------------------

def test_fails_on_invalid_json(tmp_path):
    _write_history(tmp_path, "not json")
    r = run(tmp_path)
    assert r.returncode != 0
    assert "not valid JSON" in r.stderr


def test_fails_on_empty_history(tmp_path):
    _write_history(tmp_path, [])
    r = run(tmp_path)
    assert r.returncode != 0
    assert "non-empty JSON array" in r.stderr


def test_fails_on_invalid_grade_letter(tmp_path):
    _write_history(tmp_path, [{**ENTRY, "grade": "C+"}])
    r = run(tmp_path)
    assert r.returncode != 0
    assert "invalid grade" in r.stderr


def test_fails_when_counts_are_not_non_negative_integers(tmp_path):
    _write_history(tmp_path, [{**ENTRY, "errors": "1"}])
    r = run(tmp_path)
    assert r.returncode != 0
    assert "non-negative integer" in r.stderr


def test_fails_when_run_at_is_missing(tmp_path):
    entry = {k: v for k, v in ENTRY.items() if k != "runAt"}
    _write_history(tmp_path, [entry])
    r = run(tmp_path)
    assert r.returncode != 0
    assert "runAt" in r.stderr


# --- the grade was not recorded ------------------------------------------------

def test_fails_when_history_missing_and_cli_supports_the_verb(tmp_path):
    uip = _fake_uip(tmp_path, exit_code=0)
    r = run(tmp_path, uip=uip)
    assert r.returncode != 0
    assert "Step 6" in r.stderr


def test_passes_with_warning_when_cli_lacks_the_verb(tmp_path):
    uip = _fake_uip(tmp_path, exit_code=2)
    r = run(tmp_path, uip=uip)
    assert r.returncode == 0, r.stderr
    assert "unavailable" in r.stdout
    assert "WARN" in r.stdout


def test_passes_with_warning_when_uip_is_not_on_path(tmp_path):
    r = run(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "WARN" in r.stdout


# --- report plumbing -----------------------------------------------------------

def test_fails_when_report_missing(tmp_path):
    _write_history(tmp_path, [ENTRY])
    r = run(tmp_path, report=None)
    assert r.returncode != 0
    assert "not found" in r.stderr


def test_fails_when_report_has_no_final_grade_footer(tmp_path):
    _write_history(tmp_path, [ENTRY])
    r = run(tmp_path, report="# Review Report\n\nNo footer here.\n")
    assert r.returncode != 0
    assert "Final grade" in r.stderr
