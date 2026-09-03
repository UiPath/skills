"""Unit tests for check_issue_journal.py — the incremental issue-log grader.

Fixtures are minimal synthetic stubs; no tenant, no captured artifact.
CI runs these via ``pytest tests/tasks/uipath-maestro-case/``.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_issue_journal.py")

GOOD = """# Build Issues — Stub

**Case file:** caseplan.json | **Build started:** 2026-08-13T00:00:00Z

<!--build-issues:summary:start-->
| Category | Errors | Warnings | Skipped |
|---|---|---|---|
| **Total** | **0** | **0** | **1** |
<!--build-issues:summary:end-->

## Journal

| Sev | Step | Plugin | Message |
|---|---|---|---|
| SKIPPED | 9 | connector-activity | Task "X" unresolved — placeholder emitted |
"""

NO_JOURNAL = """# Build Issues — Stub

<!--build-issues:summary:start-->
| Category | Errors |
|---|---|
| **Total** | **1** |
<!--build-issues:summary:end-->

## io-binding

| Step | Issue |
|---|---|
| 9 | something |
"""

EMPTY_JOURNAL = GOOD.split("## Journal")[0] + """## Journal

| Sev | Step | Plugin | Message |
|---|---|---|---|
"""

PLACEHOLDER_SUMMARY = GOOD.replace(
    "| Category | Errors | Warnings | Skipped |\n|---|---|---|---|\n| **Total** | **0** | **0** | **1** |",
    "_Summary written at Step 12.1._",
)

RECONSTRUCTED = GOOD.replace(
    "**Build started:**",
    "NOTE: reconstructed at Step 12.1 from on-disk artifacts — the incremental journal was not written.\n\n**Build started:**",
)


CLEAN_AUDIT = '[{"task": "Hold", "selected": {"name": "X"}}]'
# Rule 9 shape for an unresolved entry: matches [], selected null, and the
# <UNRESOLVED: reason> text in the identity slot — see
# skills/uipath-maestro-case/references/placeholder-tasks.md § registry-resolved.json Entry Shape.
UNRESOLVED_AUDIT = ('[{"task": "Hold", "taskType": "process", "matches": [], "selected": null, '
                    '"taskTypeId": "<UNRESOLVED: process not found in registry>"}]')


def caseplan(placeholder=True):
    task = {"id": "tA", "type": "wait-for-timer", "displayName": "Hold",
            "data": {} if placeholder else {"serviceType": "X"}}
    return {"id": "case-Stub000001", "version": "27.0.0", "name": "Stub", "metadata": {},
            "nodes": [{"id": "Stage_a", "type": "case-management:Stage",
                       "data": {"label": "S", "tasks": [[task]]}}], "edges": []}


def run(tmp_path, *, case=None, log=None, audit=None):
    if case is not None:
        d = tmp_path / "Sol" / "Proj"; d.mkdir(parents=True, exist_ok=True)
        (d / "caseplan.json").write_text(json.dumps(case))
    for name, content in (("build-issues.md", log), ("registry-resolved.json", audit)):
        if content is not None:
            d = tmp_path / "tasks"; d.mkdir(parents=True, exist_ok=True)
            (d / name).write_text(content)
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                          capture_output=True, text=True)


# --- the regression ------------------------------------------------------------------

def test_unresolved_work_with_no_log_fails(tmp_path):
    """Both measured runs: placeholders present, no build-issues.md at all."""
    res = run(tmp_path, case=caseplan())
    assert res.returncode == 1, res.stdout
    assert "NO tasks/build-issues.md" in res.stdout


def test_incremental_journal_passes(tmp_path):
    res = run(tmp_path, case=caseplan(), log=GOOD)
    assert res.returncode == 0, res.stdout
    assert "incremental journal" in res.stdout


# --- the incremental contract, not just existence ------------------------------------

def test_end_of_build_dump_without_journal_fails(tmp_path):
    """The OLD format — grouped sections, no journal — must not satisfy the new contract."""
    res = run(tmp_path, case=caseplan(), log=NO_JOURNAL)
    assert res.returncode == 1, res.stdout
    assert "no '## Journal' section" in res.stdout


def test_empty_journal_with_unresolved_work_fails(tmp_path):
    res = run(tmp_path, case=caseplan(), log=EMPTY_JOURNAL)
    assert res.returncode == 1, res.stdout
    assert "no rows" in res.stdout


def test_unfilled_summary_fails(tmp_path):
    res = run(tmp_path, case=caseplan(), log=PLACEHOLDER_SUMMARY)
    assert res.returncode == 1, res.stdout
    assert "placeholder summary" in res.stdout


# --- degraded but honest --------------------------------------------------------------

def test_reconstructed_log_passes_but_is_reported(tmp_path):
    res = run(tmp_path, case=caseplan(), log=RECONSTRUCTED)
    assert res.returncode == 0, res.stdout
    assert "PASS (degraded)" in res.stdout
    assert "RECONSTRUCTED" in res.stdout


# --- clean builds ---------------------------------------------------------------------

def test_clean_build_still_requires_the_journal(tmp_path):
    """The flush is unconditional — a zero-issue section still creates the file."""
    res = run(tmp_path, case=caseplan(placeholder=False), audit=CLEAN_AUDIT)
    assert res.returncode == 1, res.stdout
    assert "no unresolved work, but the flush is unconditional" in res.stdout


def test_clean_build_with_empty_journal_passes(tmp_path):
    """Zero issues and zero rows is fine — the file's existence is the signal."""
    res = run(tmp_path, case=caseplan(placeholder=False),
              audit=CLEAN_AUDIT, log=EMPTY_JOURNAL)
    assert res.returncode == 0, res.stdout


def test_build_that_never_reached_phase2_is_exempt(tmp_path):
    """Halted in Phase 1 — no caseplan, so no journal expected."""
    res = run(tmp_path, audit=UNRESOLVED_AUDIT)
    assert res.returncode == 0, res.stdout
    assert "never reached Phase 2" in res.stdout


def test_unresolved_markers_alone_require_a_journal(tmp_path):
    res = run(tmp_path, case=caseplan(placeholder=False),
              audit=UNRESOLVED_AUDIT)
    assert res.returncode == 1, res.stdout
    assert "<UNRESOLVED> marker" in res.stdout


# --- guards ----------------------------------------------------------------------------

def test_venv_copies_ignored(tmp_path):
    """A placeholder-laden caseplan inside .venv must not drive the verdict."""
    v = tmp_path / ".venv" / "s"; v.mkdir(parents=True)
    (v / "caseplan.json").write_text(json.dumps(caseplan()))
    res = run(tmp_path, case=caseplan(placeholder=False),
              audit=CLEAN_AUDIT, log=EMPTY_JOURNAL)
    assert res.returncode == 0, res.stdout
    assert "none" in res.stdout.splitlines()[0]


@pytest.mark.parametrize("header", ["| Sev | Step | Plugin | Message |",
                                    "| Severity | Step | Plugin | Message |"])
def test_header_row_is_not_counted(tmp_path, header):
    log = GOOD.replace("| Sev | Step | Plugin | Message |", header)
    res = run(tmp_path, case=caseplan(), log=log)
    assert res.returncode == 0, res.stdout
    assert "1 row(s)" in res.stdout
