"""Unit tests for check_build_issues_log.py — the Step 12.2 / Check 16 grader.

Run with ``pytest``; CI runs them via ``pytest tests/tasks/uipath-maestro-case/``.

Fixtures are minimal synthetic stubs built inline — no tenant, no captured
artifact. The grader was additionally validated against two real runs:
a 39-placeholder build with no log (fails) and the connector-halt build (passes).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_build_issues_log.py")

STUB_CTX = [
    {"name": "connectorKey", "value": "placeholder", "type": "string"},
    {"name": "operation", "value": "placeholder", "type": "string"},
]

REAL_LOG = """# Build Issues — Stub

| Category | Errors | Warnings | Skipped |
|---|---|---|---|
| io-binding | 0 | 0 | 2 |

## io-binding

| Severity | Step | Message |
|---|---|---|
| SKIPPED | 9 | Task "Do Thing" unresolved — placeholder emitted |
"""

HEADER_ONLY_LOG = """# Build Issues — Stub

**Case file:** caseplan.json | **Timestamp:** 2026-08-13T00:00:00Z

| Category | Errors | Warnings | Skipped |
|---|---|---|---|

## Open Items for User
"""


def caseplan(*, placeholder=False, stub=False):
    task = {"id": "tAAAAAAAA", "type": "wait-for-timer", "displayName": "Hold"}
    task["data"] = {} if placeholder else {"serviceType": "X"}
    stage = {
        "id": "Stage_aaaaaa",
        "type": "case-management:Stage",
        "data": {"label": "S", "tasks": [[task]]},
    }
    if stub:
        stage["data"]["entryConditions"] = [{
            "id": "Condition_a", "displayName": "E",
            "rules": [[{"id": "Rule_a", "rule": "wait-for-connector",
                        "uipath": {"context": STUB_CTX, "inputs": [], "outputs": []}}]],
        }]
    return {"id": "case-Stub000001", "version": "27.0.0", "name": "Stub",
            "metadata": {}, "nodes": [stage], "edges": []}


def run(tmp_path, *, case=None, tasks_md=None, log=None):
    if case is not None:
        proj = tmp_path / "Sol" / "Proj"
        proj.mkdir(parents=True, exist_ok=True)
        (proj / "caseplan.json").write_text(json.dumps(case))
    if tasks_md is not None:
        d = tmp_path / "tasks"
        d.mkdir(parents=True, exist_ok=True)
        (d / "tasks.md").write_text(tasks_md)
    if log is not None:
        d = tmp_path / "tasks"
        d.mkdir(parents=True, exist_ok=True)
        (d / "build-issues.md").write_text(log)
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                          capture_output=True, text=True)


# --- the regression this exists for -------------------------------------------------

def test_placeholders_without_log_fails(tmp_path):
    """Today's 39-placeholder build: unresolved work, no log at all."""
    res = run(tmp_path, case=caseplan(placeholder=True))
    assert res.returncode == 1, res.stdout
    assert "shipped NO tasks/build-issues.md" in res.stdout


def test_unresolved_markers_without_log_fails(tmp_path):
    res = run(tmp_path, case=caseplan(), tasks_md="## T01\n- id: <UNRESOLVED: process>\n")
    assert res.returncode == 1, res.stdout
    assert "1 <UNRESOLVED> marker" in res.stdout


def test_surviving_stub_without_log_fails(tmp_path):
    res = run(tmp_path, case=caseplan(stub=True))
    assert res.returncode == 1, res.stdout


def test_placeholders_with_real_log_passes(tmp_path):
    res = run(tmp_path, case=caseplan(placeholder=True), log=REAL_LOG)
    assert res.returncode == 0, res.stdout
    assert "PASS" in res.stdout


# --- "I wrote a file" is not "I recorded the work" ----------------------------------

def test_header_only_log_fails(tmp_path):
    """An empty template must not pass as a record."""
    res = run(tmp_path, case=caseplan(placeholder=True), log=HEADER_ONLY_LOG)
    assert res.returncode == 1, res.stdout
    assert "no issue entries" in res.stdout


def test_empty_log_fails(tmp_path):
    res = run(tmp_path, case=caseplan(placeholder=True), log="")
    assert res.returncode == 1, res.stdout


def test_note_line_alone_is_not_an_entry(tmp_path):
    log = "# Build Issues\n\nNOTE: reconstructed at Step 12.2 from on-disk artifacts\n"
    res = run(tmp_path, case=caseplan(placeholder=True), log=log)
    assert res.returncode == 1, res.stdout


# --- clean builds don't need a log ---------------------------------------------------

def test_clean_build_without_log_passes(tmp_path):
    res = run(tmp_path, case=caseplan(), tasks_md="## T01\n- id: real-id\n")
    assert res.returncode == 0, res.stdout
    assert "no unresolved work" in res.stdout


# --- accepted log shapes -------------------------------------------------------------

@pytest.mark.parametrize("body", [
    "# Build Issues\n\n- SKIPPED: task X unresolved\n",
    "# Build Issues\n\n## io-binding\n\n| Severity | Step | Message |\n|---|---|---|\n| SKIPPED | 9 | x |\n",
    "# Build Issues\n\nTask X was left unresolved and needs wiring.\n",
])
def test_various_real_log_shapes_pass(tmp_path, body):
    res = run(tmp_path, case=caseplan(placeholder=True), log=body)
    assert res.returncode == 0, res.stdout


def test_reconstructed_log_is_flagged_in_output(tmp_path):
    log = ("# Build Issues\n\nNOTE: reconstructed at Step 12.2 from on-disk artifacts — "
           "the in-reasoning issue log was lost.\n\n- SKIPPED: task X unresolved\n")
    res = run(tmp_path, case=caseplan(placeholder=True), log=log)
    assert res.returncode == 0, res.stdout
    assert "reconstructed log" in res.stdout


# --- environment guards ---------------------------------------------------------------

def test_venv_copies_ignored(tmp_path):
    venv = tmp_path / ".venv" / "sample"
    venv.mkdir(parents=True)
    (venv / "caseplan.json").write_text(json.dumps(caseplan(placeholder=True)))
    res = run(tmp_path, case=caseplan(), tasks_md="## T01\n- id: real\n")
    assert res.returncode == 0, res.stdout


def test_unparseable_caseplan_fails(tmp_path):
    proj = tmp_path / "Sol" / "Proj"
    proj.mkdir(parents=True)
    (proj / "caseplan.json").write_text("{ not json")
    res = subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path,
                         capture_output=True, text=True)
    assert res.returncode == 1
    assert "unparseable" in res.stdout
